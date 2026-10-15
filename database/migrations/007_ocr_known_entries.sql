-- =====================================================================
-- 007_ocr_known_entries.sql
-- Common entries, for the offline AI's pattern recognition
-- (Ocr_module/paddle_assist.py).
--
-- A vocabulary of what staff actually enter, per logbook column, and how
-- often. When PaddleOCR's reading of an unclear cell is close to a common
-- entry but not quite it (e.g. "Pregnacy" vs. "Pregnancy", "Calinon" vs.
-- "Calinan"), the AI suggests the common entry. The more often something
-- is entered, the more confidently it is suggested.
--
-- Filled automatically from two places:
--   times_from_reviews - values staff confirmed on the Logbook Review page
--   times_from_forms   - values on the PhilHealth forms when a PDF is exported
--
--   entry_type  value - the whole cell value (only logbook reviews count for
--                       whole-value suggestions; forms often word things
--                       differently from the logbook)
--               word  - one word (3+ letters, no digits)
--   source      starter - seeded below; learned - added by the system
--
-- Only text columns are kept: NAME, ADDRESS, ADMITTING DIAGNOSIS,
-- FINAL DIAGNOSIS. Dates and case numbers are unique per patient, so a
-- vocabulary doesn't help there (ocr_correction_patterns covers them).
-- Corrected patient names are only ever shown as a hint, never pre-filled.
--
-- To stop an entry being suggested, set is_active = 0 in phpMyAdmin.
--
-- Apply with:
--   mariadb -u root -h 127.0.0.1 pclaimassist_db < 007_ocr_known_entries.sql
-- (or paste it into phpMyAdmin's SQL tab)
-- =====================================================================

CREATE TABLE IF NOT EXISTS `ocr_known_entries` (
  `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,

  `category`            VARCHAR(40)  NOT NULL,
  `entry_type`          ENUM('value','word') NOT NULL,

  -- Upper-cased form used for matching ("DAVAO"), and the text as staff
  -- last entered it ("Davao").
  `entry_key`           VARCHAR(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `entry_text`          VARCHAR(191) NOT NULL,

  `times_from_reviews`  INT UNSIGNED NOT NULL DEFAULT 0,
  `times_from_forms`    INT UNSIGNED NOT NULL DEFAULT 0,
  `source`              ENUM('starter','learned') NOT NULL DEFAULT 'learned',
  `is_active`           TINYINT(1) NOT NULL DEFAULT 1,

  `created_at`          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                          ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ocr_known_entry` (`category`, `entry_type`, `entry_key`),
  KEY `idx_ocr_known_entry_lookup` (`category`, `entry_type`, `is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- ── Starter words ─────────────────────────────────────────────────────
-- Counted as if entered twice, so they are suggested from day one.

-- Obstetric words used in the diagnosis columns.
INSERT IGNORE INTO `ocr_known_entries` (`category`, `entry_type`, `entry_key`, `entry_text`, `source`)
SELECT c.category, 'word', UPPER(w.word), w.word, 'starter'
FROM (
  SELECT 'ADMITTING DIAGNOSIS' AS category UNION ALL
  SELECT 'FINAL DIAGNOSIS'
) AS c
CROSS JOIN (
  SELECT 'Pregnancy' AS word UNION ALL SELECT 'Pregnant' UNION ALL SELECT 'Uterine' UNION ALL
  SELECT 'Term' UNION ALL SELECT 'Preterm' UNION ALL SELECT 'Postterm' UNION ALL
  SELECT 'Labor' UNION ALL SELECT 'Active' UNION ALL SELECT 'Latent' UNION ALL SELECT 'Phase' UNION ALL
  SELECT 'Weeks' UNION ALL SELECT 'Delivery' UNION ALL SELECT 'Delivered' UNION ALL
  SELECT 'Spontaneous' UNION ALL SELECT 'Vaginal' UNION ALL SELECT 'Cephalic' UNION ALL
  SELECT 'Breech' UNION ALL SELECT 'Live' UNION ALL SELECT 'Baby' UNION ALL
  SELECT 'Boy' UNION ALL SELECT 'Girl' UNION ALL SELECT 'Twins' UNION ALL
  SELECT 'Prolonged' UNION ALL SELECT 'Rupture' UNION ALL SELECT 'Membranes' UNION ALL
  SELECT 'Premature' UNION ALL SELECT 'Hypertension' UNION ALL SELECT 'Preeclampsia' UNION ALL
  SELECT 'Anemia' UNION ALL SELECT 'Postpartum' UNION ALL SELECT 'Hemorrhage' UNION ALL
  SELECT 'Episiotomy' UNION ALL SELECT 'Laceration' UNION ALL SELECT 'Degree' UNION ALL
  SELECT 'Multigravida' UNION ALL SELECT 'Primigravida'
) AS w;

-- Address words: Davao City districts and common address terms.
INSERT IGNORE INTO `ocr_known_entries` (`category`, `entry_type`, `entry_key`, `entry_text`, `source`)
SELECT 'ADDRESS', 'word', UPPER(w.word), w.word, 'starter'
FROM (
  SELECT 'Purok' AS word UNION ALL SELECT 'Barangay' UNION ALL SELECT 'Brgy' UNION ALL
  SELECT 'Street' UNION ALL SELECT 'Subdivision' UNION ALL SELECT 'Village' UNION ALL
  SELECT 'Phase' UNION ALL SELECT 'Block' UNION ALL SELECT 'Lot' UNION ALL
  SELECT 'Davao' UNION ALL SELECT 'City' UNION ALL SELECT 'Poblacion' UNION ALL
  SELECT 'Talomo' UNION ALL SELECT 'Agdao' UNION ALL SELECT 'Buhangin' UNION ALL
  SELECT 'Bunawan' UNION ALL SELECT 'Paquibato' UNION ALL SELECT 'Baguio' UNION ALL
  SELECT 'Calinan' UNION ALL SELECT 'Marilog' UNION ALL SELECT 'Toril' UNION ALL
  SELECT 'Tugbok' UNION ALL SELECT 'Matina' UNION ALL SELECT 'Catalunan' UNION ALL
  SELECT 'Aplaya' UNION ALL SELECT 'Bago'
) AS w;
