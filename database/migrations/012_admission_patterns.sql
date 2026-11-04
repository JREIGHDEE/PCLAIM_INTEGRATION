-- =====================================================================
-- 012_admission_patterns.sql
-- Admission patterns: the logbook's admitting diagnosis, recognised as the
-- clinic's reason for admission (user testing #5).
--
-- Each row is one admission the logbook writes again and again ("CEPHALIC
-- IN LABOR", "POST PARTUM VISIT", "WELL BABY CARE"...). When a claim is
-- opened from a logbook scan, its admitting diagnosis is matched against
-- the clues letter by letter, so a misread like "FOR POJT PAKTUM UISIT"
-- still matches POST PARTUM VISIT (Ocr_module/philhealth/admission_patterns.py).
-- The best pattern's `reason` goes into Chief Complaint / Reason for
-- Admission, tagged "please check", and its `package` helps pick the
-- claim's package.
--
--   clues     words that give the admission away, one per line
--   reason    the clinic's wording for the reason for admission
--   package   PhilHealth package (NSDBF, NCP, ANV, PPC01, FP001, IUD) or ''
--   examples  readings staff confirmed as this admission (a JSON list),
--             learned from the card under Reason for admission
--
-- Staff change the table on PClaimAssist's "Admission patterns" page
-- (Clinic); a pattern switched off there (is_active = 0) is never
-- suggested. The rows below are the admissions seen in the clinic's
-- logbook; their wording is a starting point for the clinic to correct.
--
-- Safe to run twice (the starting rows are only added once, by name).
-- Apply with:
--   mariadb -u root -h 127.0.0.1 pclaimassist_db < 012_admission_patterns.sql
-- (or paste it into phpMyAdmin's SQL tab, as root)
-- =====================================================================

CREATE TABLE IF NOT EXISTS `admission_patterns` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`             VARCHAR(80)  NOT NULL,
  `clues`            TEXT         NOT NULL,
  `reason`           VARCHAR(191) NOT NULL,
  `package`          VARCHAR(20)  NOT NULL DEFAULT '',
  `examples`         TEXT         NULL DEFAULT NULL,
  `is_active`        TINYINT(1)   NOT NULL DEFAULT 1,
  `sort_order`       INT          NOT NULL DEFAULT 0,
  -- How often it was suggested and confirmed, and suggested but wrong.
  `times_confirmed`  INT UNSIGNED NOT NULL DEFAULT 0,
  `times_corrected`  INT UNSIGNED NOT NULL DEFAULT 0,
  `updated_by`       VARCHAR(191) NULL DEFAULT NULL,
  `created_at`       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_admission_pattern_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT IGNORE INTO `admission_patterns` (`name`, `clues`, `reason`, `package`, `sort_order`) VALUES
  ('Labor (delivery)', 'CEPHALIC IN LABOR
IN LABOR
CEPHALIC
LABOR PAINS
IN ACTIVE LABOR', 'LABOR PAINS', 'NSDBF', 10),
  ('Newborn (delivered here)', 'LIVE TERM BABY
TERM BABY BOY
TERM BABY GIRL
DELIVERED VIA NSVD TO A
MOTHER WEIGHING', 'NEWBORN CARE', 'NCP', 20),
  ('Well baby care', 'WELL BABY CARE
WELL BABY', 'WELL BABY CARE', 'NCP', 30),
  ('Postpartum visit', 'POSTPARTUM VISIT
POST PARTUM VISIT
POSTPARTUM', 'POSTPARTUM VISIT', 'PPC01', 40),
  ('Prenatal check-up', 'PRENATAL CHECK UP
PRENATAL CHECKUP
PRENATAL', 'PRENATAL CHECK-UP', 'ANV', 50),
  ('Implant insertion (PSI)', 'PSI INSERTION
PSI
IMPLANT INSERTION
SUBDERMAL IMPLANT', 'FOR PSI INSERTION', 'FP001', 60),
  ('Implant removal (PSI)', 'PSI REMOVAL
PSI REMOV
IMPLANT REMOVAL', 'FOR PSI REMOVAL', '', 70),
  ('IUD insertion', 'IUD INSERTION
IUD
INTRAUTERINE DEVICE', 'FOR IUD INSERTION', 'IUD', 80),
  ('Injectable (DMPA)', 'DMPA INJECTION
DMPA INSERTION
DMPA', 'FOR DMPA INJECTION', '', 90),
  ('Injectable (CIC)', 'CIC', 'FOR CIC INJECTION', '', 100),
  ('Pills refill', 'PILLS REFILL
REFILL', 'FOR PILLS REFILL', '', 110),
  ('Family planning', 'FAMILY PLANNING', 'FAMILY PLANNING', '', 120),
  ('Family planning counseling', 'COUNSELING
FP COUNSELING', 'FAMILY PLANNING COUNSELING', '', 130),
  ('Newborn screening / hearing test', 'HEARING TEST
NEWBORN SCREENING
BCG', 'NEWBORN HEARING TEST', '', 140);
