-- =====================================================================
-- 006_ocr_correction_patterns.sql
-- Pattern recognition memory for the offline AI (Ocr_module/paddle_assist.py).
--
-- PaddleOCR stays the OCR engine. For cells it is unsure about, the offline
-- AI fixes known PaddleOCR mistakes using the patterns in this table. Each
-- row says: in this logbook column, PaddleOCR's reading `wrong_text` was
-- confirmed by staff as `correct_text`, `times_seen` times.
--
--   pattern_type  value - the whole cell value   (wrong_text upper-cased)
--                 word  - one word               (wrong_text upper-cased)
--                 char  - one character, only used in number/date columns
--   source        starter - seeded below, so the AI helps from day one
--                 learned - added from every submitted logbook review
--
-- Rows where wrong_text = correct_text ("PaddleOCR was right") are kept on
-- purpose: a fix is only applied when it was the outcome at least 60% of
-- the time and seen at least twice, so these rows stop one-off corrections
-- from being applied everywhere.
--
-- To switch off a pattern that does more harm than good, set is_active = 0
-- in phpMyAdmin (don't delete it, or it may be learned again).
--
-- Apply with:
--   mariadb -u root -h 127.0.0.1 pclaimassist_db < 006_ocr_correction_patterns.sql
-- (or paste it into phpMyAdmin's SQL tab)
-- =====================================================================

CREATE TABLE IF NOT EXISTS `ocr_correction_patterns` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- Logbook column, as in config.TRAINING_CATEGORIES ("NAME", "BDAY", ...).
  `category`      VARCHAR(40)  NOT NULL,
  `pattern_type`  ENUM('value','word','char') NOT NULL,

  -- Binary collation: "O" and "0", or "Maria" and "MARIA", are different.
  `wrong_text`    VARCHAR(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `correct_text`  VARCHAR(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,

  `times_seen`    INT UNSIGNED NOT NULL DEFAULT 1,
  `source`        ENUM('starter','learned') NOT NULL DEFAULT 'learned',
  `is_active`     TINYINT(1) NOT NULL DEFAULT 1,

  `created_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ocr_pattern` (`category`, `pattern_type`, `wrong_text`, `correct_text`),
  KEY `idx_ocr_pattern_lookup` (`category`, `pattern_type`, `is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- ── Starter patterns ──────────────────────────────────────────────────
-- times_seen = 2: enough to be used straight away, and outweighed as soon
-- as staff correct the same reading differently a few times.

-- Letters PaddleOCR reads in place of digits in handwriting, for the
-- number and date columns. (Letters in AM/PM are never changed.)
INSERT IGNORE INTO `ocr_correction_patterns`
  (`category`, `pattern_type`, `wrong_text`, `correct_text`, `times_seen`, `source`)
SELECT c.category, 'char', m.wrong_text, m.correct_text, 2, 'starter'
FROM (
  SELECT 'CASE #' AS category UNION ALL
  SELECT 'BDAY' UNION ALL
  SELECT 'DATE & TIME OF ADMISSION' UNION ALL
  SELECT 'DATE & TIME OF DELIVERY' UNION ALL
  SELECT 'DATE & TIME OF DISCHARGE'
) AS c
CROSS JOIN (
  SELECT 'O' AS wrong_text, '0' AS correct_text UNION ALL
  SELECT 'o', '0' UNION ALL SELECT 'D', '0' UNION ALL SELECT 'Q', '0' UNION ALL
  SELECT 'l', '1' UNION ALL SELECT 'I', '1' UNION ALL SELECT 'i', '1' UNION ALL SELECT '|', '1' UNION ALL
  SELECT 'Z', '2' UNION ALL SELECT 'z', '2' UNION ALL
  SELECT 'S', '5' UNION ALL SELECT 's', '5' UNION ALL
  SELECT 'G', '6' UNION ALL SELECT 'b', '6' UNION ALL
  SELECT 'T', '7' UNION ALL
  SELECT 'B', '8' UNION ALL
  SELECT 'g', '9' UNION ALL SELECT 'q', '9'
) AS m;

-- Obstetric shorthand in the diagnosis columns, as PaddleOCR tends to
-- misread it (digits and letters swapped).
INSERT IGNORE INTO `ocr_correction_patterns`
  (`category`, `pattern_type`, `wrong_text`, `correct_text`, `times_seen`, `source`)
SELECT c.category, 'word', m.wrong_text, m.correct_text, 2, 'starter'
FROM (
  SELECT 'ADMITTING DIAGNOSIS' AS category UNION ALL
  SELECT 'FINAL DIAGNOSIS'
) AS c
CROSS JOIN (
  SELECT 'N5D' AS wrong_text, 'NSD' AS correct_text UNION ALL
  SELECT 'NS0', 'NSD' UNION ALL
  SELECT 'A0G', 'AOG' UNION ALL
  SELECT 'AO6', 'AOG' UNION ALL
  SELECT 'A06', 'AOG' UNION ALL
  SELECT 'GIPO', 'G1P0' UNION ALL
  SELECT 'G1PO', 'G1P0' UNION ALL
  SELECT 'GIP0', 'G1P0' UNION ALL
  SELECT 'G2PI', 'G2P1' UNION ALL
  SELECT 'WK5', 'wks' UNION ALL
  SELECT 'C5', 'CS'
) AS m;

-- Common address words.
INSERT IGNORE INTO `ocr_correction_patterns`
  (`category`, `pattern_type`, `wrong_text`, `correct_text`, `times_seen`, `source`)
VALUES
  ('ADDRESS', 'word', 'PUOK',   'Purok', 2, 'starter'),
  ('ADDRESS', 'word', 'PUR0K',  'Purok', 2, 'starter'),
  ('ADDRESS', 'word', 'PUROX',  'Purok', 2, 'starter'),
  ('ADDRESS', 'word', 'DAVA0',  'Davao', 2, 'starter'),
  ('ADDRESS', 'word', 'DAUAO',  'Davao', 2, 'starter'),
  ('ADDRESS', 'word', 'DAVAD',  'Davao', 2, 'starter'),
  ('ADDRESS', 'word', 'C1TY',   'City',  2, 'starter'),
  ('ADDRESS', 'word', 'CITV',   'City',  2, 'starter'),
  ('ADDRESS', 'word', 'BRGV',   'Brgy',  2, 'starter');
