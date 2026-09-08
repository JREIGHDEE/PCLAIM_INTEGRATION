# OCR Engine Comparison (PaddleOCR vs Tesseract)

Standalone tooling for the capstone's documented PaddleOCR-vs-Tesseract
comparison. Nothing here is imported by `app.py` or any Flask route — running
this never touches the production OCR workflow, the database, or
`case_sessions`.

```
benchmarks/
├── engine_adapters.py     normalized {"text","confidence","bbox"} wrapper for each engine
├── image_loader.py        loads every test image/PDF page exactly once (fairness)
├── metrics.py              CER / WER helpers (with whitespace normalization - see below)
├── compare_ocr_engines.py    the CLI script you run (warm-up + --runs live here)
├── test_data/                 put test images/PDFs here (see below)
│   ├── clean_scans/
│   ├── low_quality_scans/
│   ├── rotated_scans/
│   ├── handwritten_samples/
│   └── different_form_types/
└── results/                    generated output (gitignored)
```

## 1. Install Tesseract (one-time, per machine)

`pip install pytesseract` (already in `requirements.txt`) only installs the
Python *wrapper* — it does not install the Tesseract OCR engine itself.

**Windows:**
1. Download an installer from
   https://github.com/UB-Mannheim/tesseract/wiki (the community-maintained
   Windows build).
2. Install it (default path is typically
   `C:\Program Files\Tesseract-OCR\tesseract.exe`).
3. If `tesseract` isn't automatically on your PATH after installing, set
   `TESSERACT_CMD` in `Ocr_module/.env`:
   ```env
   TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```
   Leave it blank/unset if `tesseract` already works from a plain terminal
   (`tesseract --version`).

Nobody's machine-specific install path is hardcoded anywhere in this repo —
`config.TESSERACT_CMD` is the only place it's read from, and it defaults to
"just use PATH".

## 2. Add test images

Drop real (or properly anonymized/synthetic) scans into whichever
`test_data/<category>/` subfolder fits — categories are just for grouping in
the results, the tool doesn't treat them specially. Supported: `.png`,
`.jpg`, `.jpeg`, `.pdf` (each PDF page is benchmarked as its own entry).

This tool never generates or fabricates test images itself — add real
PhilHealth-form scans (or anonymized/synthetic equivalents) yourselves. Test
scans are gitignored by default (see `Ocr_module/.gitignore`) since they may
contain real patient information — don't force-add them without checking
with the team first.

## 3. Run it

From `Ocr_module/`, using this project's venv:

```powershell
venv\Scripts\python.exe -m benchmarks.compare_ocr_engines
```

Run one engine only (useful for isolating a slow/broken engine, or for
"PaddleOCR alone" / "Tesseract alone" runs):

```powershell
venv\Scripts\python.exe -m benchmarks.compare_ocr_engines --engines paddle
venv\Scripts\python.exe -m benchmarks.compare_ocr_engines --engines tesseract
```

Custom input/output folders:

```powershell
venv\Scripts\python.exe -m benchmarks.compare_ocr_engines --input benchmarks\test_data\clean_scans --output benchmarks\results\clean_only
```

Run each image through each engine multiple times, for more stable timing
statistics (see **Repeated runs** below):

```powershell
venv\Scripts\python.exe -m benchmarks.compare_ocr_engines --runs 3
```

## 4. Output

- **`results/comparison_results.csv`** — the aggregated view, **one row per
  (image, engine)** regardless of `--runs`:
  ```
  image_name, category, ocr_engine, runs,
  mean_processing_time_seconds, min_processing_time_seconds,
  max_processing_time_seconds, stdev_processing_time_seconds,
  average_confidence, detected_text_regions, extracted_text, error
  ```
  `average_confidence`/`detected_text_regions`/`extracted_text` are taken
  from the first successful run of that pair — see **Repeated runs** for why
  that's expected to be stable across runs, and what it means when it isn't.
  This is the file to use for reporting per-image results.
- **`results/comparison_results_runs.csv`** — the raw view, **one row per
  (image, engine, run)**:
  ```
  image_name, category, ocr_engine, run_index,
  processing_time_seconds, detected_text_regions,
  average_confidence, extracted_text, error
  ```
  This is what `comparison_results.csv`'s stats are computed from — keep it
  alongside your capstone data if you want to show the underlying
  measurements, not just the aggregates.
- **`results/raw/<image>__<engine>.json`** — the full per-region output
  (text, confidence, bounding box) for every run of that image/engine, for
  debugging or deeper analysis than the CSVs allow.
- **`results/accuracy_results.csv`** — only written if `--ground-truth` was
  given (see below): `image_name, ocr_engine, character_error_rate,
  word_error_rate, character_accuracy_percent, word_accuracy_percent`. The
  `_accuracy_percent` columns are `100 * (1 - error_rate)` — the same
  accuracy-percentage formulation as the Nazeem et al. (2024, ICON) study
  cited in **Related literature** below, so a number like `92.0` here is
  directly comparable to their published `92%` figure, not a differently
  defined "confidence."

Nothing under `results/` is committed to Git (gitignored) since it's
regenerated output, not source.

## 5. Accuracy scoring (optional, requires real ground truth)

Nothing here fabricates ground-truth text. To score Character Error Rate
(CER) and Word Error Rate (WER), prepare a CSV yourself with manually
verified transcriptions:

```csv
image_name,correct_text
sample1.png,"John Dela Cruz\n123 Rizal St."
sample2.png#page1,"Confinement Form..."
```

- `image_name` must exactly match the name shown in `comparison_results.csv`
  (PDF pages are named `<filename>#page<N>`).
- `correct_text` is the full expected transcription of everything on that
  page, in reading order.

Then:

```powershell
venv\Scripts\python.exe -m benchmarks.compare_ocr_engines --ground-truth benchmarks\ground_truth.csv
```

This scores whole-page CER/WER only. Per-field accuracy (matching the
`research_ground_truth`/`research_ocr_results` table schema already defined
in `database/schema.sql`) would need each field's text isolated first (via
the existing template engine's cell cropping) before scoring — that's a
natural next step, but out of scope for this preparation pass since it would
mean touching `template_engine.py`/`batch_processor.py`, which this task was
explicitly scoped to leave alone.

## Experimental methodology

This section documents exactly what the benchmark measures and why, so it
can be cited/described accurately in the capstone write-up.

### Warm-up

Before any test image is processed, `run_benchmark()` runs one throwaway
OCR call per selected engine on a small in-memory synthetic image (plain
white, 256×64, generated in code — never a real test image, never written
to any output file, and never included in any CSV, JSON, mean, min, max, or
stdev).

This exists because the two engines have fundamentally different start-up
architectures:

- **PaddleOCR** (`ocr_engine.get_ocr_engine()`) lazily constructs its model
  exactly once per process, the first time it's called. Measured on this
  machine, that first call took **2.18s**, versus **~0.11s** for every call
  after — a ~19× one-time cost. Without a warm-up, whichever test image
  happened to be processed first would silently absorb that cost into its
  `processing_time_seconds`, making it look far slower than it actually is.
  The warm-up call triggers that one-time construction before timing starts,
  so every recorded measurement reflects steady-state inference only.
- **Tesseract** (via pytesseract) has no equivalent to exclude: every call
  invokes `tesseract.exe` as a **fresh subprocess**, so there is no
  persistent in-process model state that a warm-up could "load in advance."
  Its warm-up call is still made, purely so the very first *real*
  measurement isn't the one paying for any one-time OS-level disk-cache
  warming of the tessdata files — but architecturally, Tesseract's first
  real call and its hundredth are the same kind of operation.

In other words: the benchmark measures **each engine's own normal
steady-state architecture** — PaddleOCR's warm in-process inference, and
Tesseract's per-call subprocess invocation (which is not a "cold start" for
Tesseract, just how it always runs). This is a real, disclosed difference
between the engines, not something the benchmark hides or evens out.

### Timing boundary

For every run, `time.perf_counter()` wraps exactly this:

```
Already-decoded image array (numpy, in memory)
  → OCR engine call (run_paddle() / run_tesseract())
  → OCR regions returned
```

Image decoding (`cv2.imread` / PDF page rendering) happens earlier, in
`image_loader.py`, **outside** the timed section, identically for both
engines — so decode cost never enters either engine's measured time.

One engine-specific step happens *inside* the timed window for Tesseract
only: `run_tesseract()` converts the array from OpenCV's BGR channel order
to RGB (`cv2.cvtColor`) before calling pytesseract, which otherwise
interprets a raw ndarray as if it were already RGB — without this
conversion, Tesseract would see color-swapped input, which is a real
correctness issue, not an optional preprocessing choice. PaddleOCR needs no
such conversion. Measured on this machine, that conversion takes
**~8 microseconds**, against ~110–180ms of actual OCR per call (roughly
0.005–0.01% of the measurement) — negligible, but documented here rather
than left unstated, since it is genuinely asymmetric between the two
engines' timed code paths.

### Repeated runs

`--runs N` (default `1`, so the plain `compare_ocr_engines` command is
unchanged) repeats OCR **N times per (image, engine) pair**, independently
of every other image and every other engine — run counts, means, and
extremes are never pooled across different images or different engines.

- Every individual run's timing is written to
  `comparison_results_runs.csv` (one row per image × engine × run).
- `comparison_results.csv` holds the aggregate for each (image, engine)
  pair: `runs`, `mean_processing_time_seconds`, `min_processing_time_seconds`,
  `max_processing_time_seconds`, and `stdev_processing_time_seconds` (`None`
  when fewer than 2 runs succeeded — standard deviation is undefined for a
  single sample).
- Stats are computed only from **successful** runs; if some runs errored
  and others succeeded, the aggregate row's `error` column notes how many
  failed (e.g. `"1/3 runs failed: ..."`) while timing stats still reflect
  the runs that worked. If every run failed, timing stats are `None` and
  `error` holds the failure message.
- `average_confidence` / `detected_text_regions` / `extracted_text` in the
  aggregate row come from the first successful run. Neither engine has any
  randomness in its inference (no sampling/dropout at inference time), so
  repeated runs on the same image are expected to produce identical output
  — only wall-clock time should vary run to run. If a difference is ever
  detected between successful runs anyway, the aggregate row's `error`
  column is set to a warning (`"warning: extracted_text differed across ..."`)
  rather than silently picking one — that would itself be worth
  investigating before trusting the benchmark's numbers.

### CER / WER whitespace normalization

Before computing CER or WER (`benchmarks/metrics.py`), both the reference
(ground truth) and the hypothesis (OCR output) have all whitespace runs —
spaces, tabs, newlines — collapsed to a single space, and are trimmed at
both ends. Nothing else is touched: case, punctuation, digits, and every
other character are scored exactly as recognized/transcribed.

This exists to cancel out a benchmark artifact, not a real accuracy
difference: PaddleOCR's regions are line/phrase-level, while Tesseract's
(`image_to_data`) are word-level, and `extracted_text` joins each engine's
own regions with `"\n"`. So for the exact same correctly-recognized text:

```
PaddleOCR (one region for the whole line): "Juan Dela Cruz"
Tesseract (one region per word):           "Juan\nDela\nCruz"
```

Without normalization, these would be scored as different text — not
because either engine misread anything, but purely because of how many
regions each engine happened to split the same line into. Measured
directly: with identical, 100%-correct words, the un-normalized CER came
out to `0.0` for the line-level join and `0.04` for the word-level join,
for text that was equally correct. Whitespace normalization makes both
forms equivalent, applied identically to both engines and to the ground
truth, so it cannot favor either engine — it only removes a formatting
artifact from how this benchmark happens to reconstruct page text from
per-region output.

### Accuracy percentage (matching Nazeem et al., 2024)

Alongside the raw `character_error_rate`/`word_error_rate`,
`accuracy_results.csv` also reports `character_accuracy_percent` and
`word_accuracy_percent` — computed as `100 * (1 - error_rate)`, using the
exact same WER/CER formulas above. This intentionally matches how Nazeem,
R, S, & R. R (2024, ICON — see **Related literature** below) report OCR
"accuracy" in their Table I (e.g. their `92%` for Tesseract OCR on
English), so this benchmark's numbers are directly comparable to a
published figure using the same metric definition, rather than to each
engine's own internal, self-reported per-detection confidence score
(`average_confidence` in `comparison_results.csv`) — which measures the
engine's certainty in its own output, not measured correctness against
ground truth. The two are answering different questions:

- `average_confidence` — "how sure was the engine, in its own estimation?"
  (native score, normalized to 0–1, no ground truth involved)
- `word_accuracy_percent` / `character_accuracy_percent` — "how much of the
  ground truth did the engine actually get right?" (requires `--ground-truth`)

Values are clamped to `[0, 100]`: WER/CER can technically exceed `1.0` when
the hypothesis has far more inserted text than the reference has words/
characters, which would otherwise produce a negative "accuracy" that isn't
meaningful on the paper's 0–100% scale.

### Other fairness properties (unchanged from the previous review)

- Both engines receive the exact same decoded image array for a given file
  (see `image_loader.py`) — neither re-reads the file independently, and
  neither mutates the shared array (verified by hashing it before/after
  each engine call).
- No extra preprocessing (denoising, thresholding, deskewing, etc.) is
  applied before either engine — this matches how the production PaddleOCR
  pipeline already works (`ocr_engine.py` does no preprocessing either).
- Confidence scores are normalized to a common 0–1 scale (Tesseract natively
  reports 0–100; PaddleOCR already reports 0–1) so `average_confidence` is
  comparable between engines.
- For a fair head-to-head, run both engines in the same benchmark
  invocation, on the same machine, without other heavy processes competing
  for CPU — absolute times are only meaningful relative to each other on
  the same run/machine, not as portable numbers.

## Known limitations (still present after this review)

- Timing reflects **this machine's** CPU, load, and installed library
  versions only — not a general "PaddleOCR is faster than Tesseract"
  claim. Re-running on different hardware could change results.
- Tesseract's per-call subprocess overhead (process spawn, tessdata load)
  is included in every one of its measurements, by design — that is
  Tesseract's real steady-state behavior via pytesseract, not a bug to work
  around (see **Warm-up** above). A different Tesseract integration (e.g.
  the `tesserocr` library, which keeps a persistent in-process instance)
  would likely show different numbers; that's a different tool, not
  evaluated here.
- Only whole-page CER/WER is supported. Per-field accuracy — matching the
  `research_ground_truth`/`research_ocr_results` tables already defined in
  `database/schema.sql` — would need each field's text isolated first (via
  the existing template engine's cell cropping), which is out of scope here
  since it would mean touching `template_engine.py`/`batch_processor.py`.
- Region granularity itself (line-level vs. word-level) is still visible in
  `detected_text_regions` and in the raw per-region JSON — whitespace
  normalization only affects the CER/WER text comparison, not the region
  counts or bounding boxes, which are reported as each engine actually
  returned them.

## Related literature (for capstone documentation)

For grounding this benchmark's methodology and results against published
work, rather than relying only on vendor blog posts, I looked for a
peer-reviewed study that (a) evaluates both PaddleOCR and Tesseract
specifically, and (b) uses accuracy metrics comparable to this benchmark's
own CER/WER. Being transparent about what was and wasn't found:

### Primary reference — closest match found

> Nazeem, M., R, A., S, N., & R. R, R. (2024). **Open-Source OCR Libraries:
> A Comprehensive Study for Low Resource Language.** In S. Lalitha Devi &
> K. Arora (Eds.), *Proceedings of the 21st International Conference on
> Natural Language Processing (ICON)* (pp. 416–421). NLP Association of
> India (NLPAI). https://aclanthology.org/2024.icon-1.48/

```bibtex
@inproceedings{nazeem-etal-2024-open,
    title     = "Open-Source {OCR} Libraries: A Comprehensive Study for Low Resource Language",
    author    = "Nazeem, Meharuniza and R, Anitha and S, Navaneeth and R. R, Rajeev",
    editor    = "Lalitha Devi, Sobha and Arora, Karunesh",
    booktitle = "Proceedings of the 21st International Conference on Natural Language Processing (ICON)",
    month     = dec,
    year      = "2024",
    address   = "AU-KBC Research Centre, Chennai, India",
    publisher = "NLP Association of India (NLPAI)",
    pages     = "416--421"
}
```

Why this is the closest verifiable match:
- It benchmarks **Tesseract OCR and PaddleOCR directly against each other**
  (alongside MMOCR, EasyOCR, and Keras OCR) — the same engine pair as this
  project.
- It scores accuracy using **the same metrics this benchmark uses**: Word
  Error Rate (`WER = (S+I+D)/N`) and Character Error Rate via Levenshtein
  distance (`CER = (S+I+D)/N`) — i.e. `benchmarks/metrics.py` in this repo
  implements the same formulas, not a different notion of "accuracy."
- Their reported **English-language** accuracy (the closest of their five
  tested languages to this project's forms): **Tesseract OCR 92%, PaddleOCR
  89%** (their Table I; other languages tested were Hindi, Tamil, Arabic,
  and Malayalam, where the ranking sometimes reverses — PaddleOCR beat
  Tesseract on Arabic in their results).

Where it honestly does **not** match this project, so it isn't overstated
in your write-up:
- Their dataset is general **scanned documents, camera images, and PDFs**
  gathered manually/via web-scraping across multiple languages — not
  structured medical/insurance claim forms. It supports "PaddleOCR and
  Tesseract are both credible, competitive engines worth comparing," not
  "here is PhilHealth-form-specific accuracy." The authors acknowledge
  this limitation themselves, in their own words: *"the evaluation
  findings may change based on the dataset, languages, and particular use
  cases."* That's directly useful
  for your capstone: it's the literature's own admission that engine
  ranking is domain-dependent, which is exactly why a PhilHealth-form-
  specific benchmark (this repo's `compare_ocr_engines.py`) is a
  worthwhile, non-redundant contribution rather than a repeat of existing
  work.

### Other literature considered, and why they were set aside

- Soni, V. K., Shukla, V., Tandan, S. R., Pimpalkar, A., Nema, N. K., &
  Naik, M. (2025). *Performance Evaluation of Efficient and Accurate Text
  Detection and Recognition in Natural Scenes Images Using EAST and OCR
  Fusion.* International Journal of Advanced Computer Science and
  Applications, 16(1), 445–453. https://thesai.org/Downloads/Volume16No1/Paper_44-Performance_Evaluation_of_Efficient_and_Accurate_Text_Detection.pdf
  — reports average confidence scores of 0.85 (EasyOCR), 0.89 (Tesseract),
  0.93 (PaddleOCR), which sounds directly relevant. **Set aside as the
  primary citation** because their test data is natural-scene photos (e.g.
  building signage, via ICDAR2013/2015 and COCO-Text) processed through
  the EAST scene-text detector first — a different task (scene text "in
  the wild") from scanned/printed document OCR, and their confidence
  figures come from a very small sample (three test images). Still
  citable as evidence that PaddleOCR's confidence scores trend higher than
  Tesseract's across tasks generally, just not as a form-OCR benchmark.
- Sinha, R., & B S, R. (2025). *Digitization of Document and Information
  Extraction using OCR.* arXiv:2506.11156. https://arxiv.org/abs/2506.11156
  — a closer domain match (scanned documents/PDFs, confidence-annotated
  output), but compares Tesseract, DocTR, and Google Vision API — it does
  **not** evaluate PaddleOCR at all, so it can't support a PaddleOCR-vs-
  Tesseract claim. Useful only as general background on OCR+LLM
  confidence-scoring pipelines, not as an engine-comparison citation. Also
  note it's an arXiv preprint, not peer-reviewed, unlike the ICON 2024 and
  IJACSA papers above.

No published, peer-reviewed study specifically benchmarking PaddleOCR vs.
Tesseract on structured medical/insurance claim forms was found — which is
worth stating plainly in the capstone's literature review as the gap this
project's own benchmark addresses, rather than implying one exists.
