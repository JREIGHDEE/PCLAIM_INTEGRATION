"""Per-form PDF field coordinate maps.

Each module (cf2.py, csf.py) is a mechanical, value-for-value port of the
corresponding PClaimAssist/js/pdf/overlays/<form>.js file - same field ids,
keys, page numbers, and top/left/w/fs percentages (percent of rendered page,
derived from actual PDF text/rect extraction by that project). Do not hand-
tune these without re-deriving from the JS source or the real PDF - they are
the actual calibrated positions PClaimAssist's own export already uses.
"""
from philhealth.overlays.cf2 import CF2_OVERLAY
from philhealth.overlays.csf import CSF_OVERLAY

OVERLAYS = {
    "cf2": CF2_OVERLAY,
    "csf": CSF_OVERLAY,
}
