-- =====================================================================
-- PClaimAssist / OCR Module — Approved MVP Database Schema
-- Target: XAMPP MariaDB/MySQL (InnoDB, utf8mb4)
-- 8 tables: patients, case_sessions, encounters, claims,
--           claim_prenatal_visits, claim_postpartum_care,
--           research_ground_truth, research_ocr_results
--
-- NOTE: 8 CF3/PMRF-only `claims` columns (civil_status, citizenship,
-- mobile, lmp, delivery_date, manner_of_delivery, fetal_outcome,
-- birth_weight) were relaxed from NOT NULL to nullable so a 'draft' claim
-- can be created from CF2/CSF data alone (the PhilHealth claim-form
-- population feature builds CF2+CSF first; CF3/PMRF are a later phase).
-- An existing database created from an earlier copy of this file needs
-- database/migrations/001_relax_pmrf_cf3_not_null.sql applied.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `pclaimassist_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `pclaimassist_db`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- 1. patients
-- ---------------------------------------------------------------------
CREATE TABLE `patients` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `last_name`     VARCHAR(100) NOT NULL,
  `first_name`    VARCHAR(100) NOT NULL,
  `middle_name`   VARCHAR(100) NULL DEFAULT NULL,
  `name_ext`      VARCHAR(10)  NULL DEFAULT NULL,
  `date_of_birth` DATE         NOT NULL,
  `sex`           ENUM('Male','Female') NULL DEFAULT NULL,
  `pin`           VARCHAR(20)  NULL DEFAULT NULL,
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 2. case_sessions
-- ---------------------------------------------------------------------
CREATE TABLE `case_sessions` (
  `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `logbook_case_number` VARCHAR(50)  NULL DEFAULT NULL,
  `case_name`           VARCHAR(255) NULL DEFAULT NULL,
  `reviewed_values`     JSON         NOT NULL,
  `source_document`     VARCHAR(500) NULL DEFAULT NULL,
  `reviewed_at`         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 3. encounters
-- ---------------------------------------------------------------------
CREATE TABLE `encounters` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `patient_id`       INT UNSIGNED NOT NULL,
  `case_session_id`  INT UNSIGNED NULL DEFAULT NULL,
  `date_admitted`    DATE         NOT NULL,
  `time_admitted`    VARCHAR(5)   NULL DEFAULT NULL,
  `am_pm_admitted`   ENUM('AM','PM') NULL DEFAULT NULL,
  `date_discharge`   DATE         NULL DEFAULT NULL,
  `time_discharge`   VARCHAR(5)   NULL DEFAULT NULL,
  `am_pm_discharge`  ENUM('AM','PM') NULL DEFAULT NULL,
  `disposition`      ENUM('Improved','Recovered','Transferred','HAMA','Absconded','Expired') NULL DEFAULT NULL,
  `accommodation`    ENUM('Non-Private','Private','Ward','ICU/NICU') NULL DEFAULT NULL,
  `chief_complaint`  TEXT         NULL DEFAULT NULL,
  `admission_dx`     TEXT         NULL DEFAULT NULL,
  `discharge_dx`     TEXT         NULL DEFAULT NULL,
  `created_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_encounters_case_session` (`case_session_id`),
  CONSTRAINT `fk_encounters_patient`
    FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_encounters_case_session`
    FOREIGN KEY (`case_session_id`) REFERENCES `case_sessions` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 4. claims
-- ---------------------------------------------------------------------
CREATE TABLE `claims` (
  -- system / link -------------------------------------------------
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `encounter_id`     INT UNSIGNED NOT NULL,
  `status`           ENUM('draft','ready','exported') NOT NULL DEFAULT 'draft',
  `created_at`       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  -- member info (CSF, PMRF) ----------------------------------------
  -- Nullable: these are CSF-required fields for export validation, but have
  -- no OCR/patient source data - they can only ever be filled by manual
  -- entry, so a claim must be able to exist (in 'draft' status) before they
  -- are - see database/migrations/001_relax_pmrf_cf3_not_null.sql
  `member_last_name`   VARCHAR(100) NULL DEFAULT NULL,
  `member_first_name`  VARCHAR(100) NULL DEFAULT NULL,
  `member_middle_name` VARCHAR(100) NULL DEFAULT NULL,
  `member_name_ext`    VARCHAR(10)  NULL DEFAULT NULL,
  `member_dob`         DATE         NULL DEFAULT NULL,
  `member_sex`         ENUM('Male','Female') NULL DEFAULT NULL,
  `member_pin`         VARCHAR(20)  NULL DEFAULT NULL,
  `relationship`       ENUM('Self','Spouse','Child','Parent','Sibling') NULL DEFAULT NULL,

  -- HCI / facility (CF2, CF3) ---------------------------------------
  `hci_pan`      VARCHAR(20)  NOT NULL,
  `hci_name`     VARCHAR(255) NOT NULL,
  `hci_street`   VARCHAR(255) NULL DEFAULT NULL,
  `hci_city`     VARCHAR(100) NULL DEFAULT NULL,
  `hci_province` VARCHAR(100) NULL DEFAULT NULL,

  -- employer (CSF) ---------------------------------------------------
  `employer_pen`   VARCHAR(50)  NULL DEFAULT NULL,
  `employer_phone` VARCHAR(20)  NULL DEFAULT NULL,
  `employer_name`  VARCHAR(255) NULL DEFAULT NULL,

  -- member profile (PMRF) --------------------------------------------
  -- civil_status/citizenship are PMRF-only fields; nullable so a claim can
  -- exist in 'draft' status (see `status` above) before PMRF data is
  -- collected - see database/migrations/001_relax_pmrf_cf3_not_null.sql
  `civil_status`       ENUM('Single','Married','Widowed','Legally Separated','Annulled') NULL DEFAULT NULL,
  `place_of_birth`     VARCHAR(255) NULL DEFAULT NULL,
  `citizenship`        VARCHAR(100) NULL DEFAULT NULL,
  `mother_last_name`   VARCHAR(100) NULL DEFAULT NULL,
  `mother_first_name`  VARCHAR(100) NULL DEFAULT NULL,
  `mother_middle_name` VARCHAR(100) NULL DEFAULT NULL,
  `spouse_last_name`   VARCHAR(100) NULL DEFAULT NULL,
  `spouse_first_name`  VARCHAR(100) NULL DEFAULT NULL,
  `spouse_middle_name` VARCHAR(100) NULL DEFAULT NULL,
  -- member_type is PMRF-only; nullable for the same draft-claim reason as
  -- civil_status/citizenship above.
  `member_type` ENUM(
    'Employed Private','Employed Government','Self-Earning Individual',
    'OFW Land-Based','OFW Sea-Based','Lifetime Member',
    'Senior Citizen','Indigent/Sponsored'
  ) NULL DEFAULT NULL,
  `profession`      VARCHAR(100) NULL DEFAULT NULL,
  `monthly_income`  VARCHAR(50)  NULL DEFAULT NULL,

  -- address & contact (PMRF) ------------------------------------------
  `addr_street`       VARCHAR(100) NULL DEFAULT NULL,
  `addr_subdivision`  VARCHAR(100) NULL DEFAULT NULL,
  `addr_barangay`     VARCHAR(100) NULL DEFAULT NULL,
  `addr_city`         VARCHAR(100) NULL DEFAULT NULL,
  `addr_province`     VARCHAR(100) NULL DEFAULT NULL,
  `addr_zip`          VARCHAR(100) NULL DEFAULT NULL,
  -- mobile is a PMRF-only field; nullable for the same draft-claim reason
  -- as civil_status/citizenship above.
  `mobile`            VARCHAR(20)  NULL DEFAULT NULL,
  `home_phone`        VARCHAR(20)  NULL DEFAULT NULL,
  `addr_unit`         VARCHAR(100) NULL DEFAULT NULL,
  `addr_building`     VARCHAR(100) NULL DEFAULT NULL,
  `addr_lot`          VARCHAR(100) NULL DEFAULT NULL,
  `email`             VARCHAR(100) NULL DEFAULT NULL,

  -- maternity / delivery (CF3) -----------------------------------------
  -- These are CF3-only fields; nullable so a claim can exist in 'draft'
  -- status before CF3 data is collected (v1 only builds CF2+CSF) - see
  -- database/migrations/001_relax_pmrf_cf3_not_null.sql
  `lmp`                DATE         NULL DEFAULT NULL,
  `age_of_menarche`    DECIMAL(4,1) NULL DEFAULT NULL,
  `gravida`            SMALLINT UNSIGNED NULL DEFAULT NULL,
  `para`               SMALLINT UNSIGNED NULL DEFAULT NULL,
  `expected_dd`        DATE         NULL DEFAULT NULL,
  `delivery_date`      DATE         NULL DEFAULT NULL,
  `delivery_time`      VARCHAR(5)   NULL DEFAULT NULL,
  `am_pm_delivery`     ENUM('AM','PM') NULL DEFAULT NULL,
  `manner_of_delivery` ENUM(
    'Normal Spontaneous Delivery (NSD)','Caesarean Section (CS)',
    'Vacuum Extraction','Forceps Delivery','Breech Delivery'
  ) NULL DEFAULT NULL,
  `fetal_outcome` ENUM('Live Birth','Stillbirth','Abortion','Ectopic Pregnancy') NULL DEFAULT NULL,
  `baby_sex`      ENUM('Male','Female') NULL DEFAULT NULL,
  `birth_weight`  VARCHAR(20)  NULL DEFAULT NULL,
  `apgar_score`   DECIMAL(4,1) NULL DEFAULT NULL,
  `brief_history` TEXT NULL DEFAULT NULL,

  -- physical exam (CF3) --------------------------------------------------
  `vital_bp`             VARCHAR(20) NULL DEFAULT NULL,
  `vital_cr`              VARCHAR(20) NULL DEFAULT NULL,
  `vital_rr`               VARCHAR(20) NULL DEFAULT NULL,
  `vital_temp`             VARCHAR(20) NULL DEFAULT NULL,
  `pe_heent`               TEXT NULL DEFAULT NULL,
  `pe_abdomen`             TEXT NULL DEFAULT NULL,
  `pe_chest_lungs`         TEXT NULL DEFAULT NULL,
  `pe_gu`                  TEXT NULL DEFAULT NULL,
  `pe_cvs`                 TEXT NULL DEFAULT NULL,
  `pe_skin_extremities`    TEXT NULL DEFAULT NULL,
  `pe_neuro_exam`          TEXT NULL DEFAULT NULL,

  -- course / labs (CF3) ----------------------------------------------------
  `course_in_wards` TEXT NULL DEFAULT NULL,
  `lab_findings`    TEXT NULL DEFAULT NULL,

  -- CF3 page 2 — maternity care package header -----------------------------
  `initial_prenatal_date`     DATE NULL DEFAULT NULL,
  `vital_signs_normal`        BOOLEAN NOT NULL DEFAULT FALSE,
  `pregnancy_low_risk`        BOOLEAN NOT NULL DEFAULT FALSE,
  `ob_term`                   SMALLINT UNSIGNED NULL DEFAULT NULL,
  `ob_preterm`                SMALLINT UNSIGNED NULL DEFAULT NULL,
  `ob_abortion`               SMALLINT UNSIGNED NULL DEFAULT NULL,
  `ob_living`                 SMALLINT UNSIGNED NULL DEFAULT NULL,

  -- 20 fixed risk-factor flags --------------------------------------------
  `risk_multiple_pregnancy`     BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_ovarian_cyst`           BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_myoma_uteri`            BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_placenta_previa`        BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_miscarriages`           BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_stillbirth`             BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_preeclampsia`           BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_eclampsia`              BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_premature_contraction`  BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_hypertension`           BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_heart_disease`          BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_diabetes`               BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_thyroid_disorder`       BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_obesity`                BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_asthma`                 BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_epilepsy`               BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_renal_disease`          BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_bleeding_disorders`     BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_prev_cesarian`          BOOLEAN NOT NULL DEFAULT FALSE,
  `risk_uterine_myomectomy`     BOOLEAN NOT NULL DEFAULT FALSE,

  -- remaining CF3 page 2 fields ---------------------------------------------
  `mcp_orientation`            ENUM('yes','no') NULL DEFAULT NULL,
  `obstetric_index`            VARCHAR(50)  NULL DEFAULT NULL,
  `pregnancy_uterine_aog`      VARCHAR(50)  NULL DEFAULT NULL,
  `presentation`               VARCHAR(100) NULL DEFAULT NULL,
  `postpartum_followup_date`   DATE NULL DEFAULT NULL,
  `attending_physician_name`   VARCHAR(255) NULL DEFAULT NULL,
  `date_signed`                DATE NULL DEFAULT NULL,

  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_claims_encounter` (`encounter_id`),
  CONSTRAINT `fk_claims_encounter`
    FOREIGN KEY (`encounter_id`) REFERENCES `encounters` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 5. claim_prenatal_visits
-- ---------------------------------------------------------------------
CREATE TABLE `claim_prenatal_visits` (
  `id`           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `claim_id`     INT UNSIGNED NOT NULL,
  `visit_number` TINYINT UNSIGNED NOT NULL COMMENT 'expected range 2-12',
  `visit_date`   DATE NULL DEFAULT NULL,
  `aog`          VARCHAR(20) NULL DEFAULT NULL,
  `weight`       DECIMAL(5,2) NULL DEFAULT NULL,
  `cr`           VARCHAR(10) NULL DEFAULT NULL,
  `rr`           VARCHAR(10) NULL DEFAULT NULL,
  `bp`           VARCHAR(10) NULL DEFAULT NULL,
  `temp`         DECIMAL(4,1) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_prenatal_claim_visit` (`claim_id`, `visit_number`),
  CONSTRAINT `fk_prenatal_claim`
    FOREIGN KEY (`claim_id`) REFERENCES `claims` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 6. claim_postpartum_care
-- ---------------------------------------------------------------------
CREATE TABLE `claim_postpartum_care` (
  `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `claim_id`   INT UNSIGNED NOT NULL,
  `care_item`  ENUM(
    'perineal','complications','breastfeeding','family_planning',
    'fp_service','referred_vss','schedule_next'
  ) NOT NULL,
  `done`       BOOLEAN NOT NULL DEFAULT FALSE,
  `remarks`    TEXT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_postpartum_claim_item` (`claim_id`, `care_item`),
  CONSTRAINT `fk_postpartum_claim`
    FOREIGN KEY (`claim_id`) REFERENCES `claims` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 7. research_ground_truth
-- ---------------------------------------------------------------------
CREATE TABLE `research_ground_truth` (
  `id`           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `source_image` VARCHAR(500) NOT NULL,
  `field_name`   VARCHAR(100) NOT NULL,
  `correct_text` TEXT NOT NULL,
  `created_at`   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_groundtruth_image_field` (`source_image`, `field_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 8. research_ocr_results
-- ---------------------------------------------------------------------
CREATE TABLE `research_ocr_results` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `ground_truth_id`  INT UNSIGNED NOT NULL,
  `engine`           ENUM('paddleocr','tesseract') NOT NULL,
  `extracted_text`   TEXT NULL DEFAULT NULL,
  `confidence`       FLOAT NULL DEFAULT NULL,
  `is_correct`       BOOLEAN NULL DEFAULT NULL,
  `error_type`       ENUM(
    'correct','misread_character','missed_field',
    'wrong_segmentation','blank_output','other'
  ) NULL DEFAULT NULL,
  `created_at`        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ocrresult_groundtruth_engine` (`ground_truth_id`, `engine`),
  CONSTRAINT `fk_ocrresult_groundtruth`
    FOREIGN KEY (`ground_truth_id`) REFERENCES `research_ground_truth` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
