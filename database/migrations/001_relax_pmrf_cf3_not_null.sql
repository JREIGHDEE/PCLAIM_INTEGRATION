-- =====================================================================
-- Migration 001: relax CF3/PMRF/CSF-manual-only `claims` columns from
-- NOT NULL to nullable.
--
-- Why: the PhilHealth claim-form population feature (v1) builds CF2+CSF
-- first; CF3/PMRF are a later phase, and even within CSF, member info
-- (member_pin, member_last_name/first_name/dob, relationship) has no
-- OCR/patient source data - it can only ever be filled by manual entry.
-- As originally written, all of these columns were NOT NULL with no
-- default, which made it impossible to INSERT a `claims` row at all for a
-- CF2/CSF-only draft claim - even though `claims.status` already has a
-- 'draft' state implying partial/incomplete claims are an expected, normal
-- thing.
--
-- Apply this once against an existing pclaimassist_db that was created
-- from an earlier copy of database/schema.sql. A fresh database created
-- from the current schema.sql already has these columns nullable and does
-- not need this file.
-- =====================================================================

USE `pclaimassist_db`;

ALTER TABLE `claims`
  -- CSF member info - manual-only, no source data
  MODIFY COLUMN `member_last_name`  VARCHAR(100) NULL DEFAULT NULL,
  MODIFY COLUMN `member_first_name` VARCHAR(100) NULL DEFAULT NULL,
  MODIFY COLUMN `member_dob`        DATE NULL DEFAULT NULL,
  MODIFY COLUMN `member_pin`        VARCHAR(20) NULL DEFAULT NULL,
  MODIFY COLUMN `relationship`      ENUM('Self','Spouse','Child','Parent','Sibling') NULL DEFAULT NULL,
  -- PMRF-only
  MODIFY COLUMN `civil_status` ENUM('Single','Married','Widowed','Legally Separated','Annulled') NULL DEFAULT NULL,
  MODIFY COLUMN `citizenship`  VARCHAR(100) NULL DEFAULT NULL,
  MODIFY COLUMN `mobile`       VARCHAR(20)  NULL DEFAULT NULL,
  MODIFY COLUMN `member_type` ENUM(
    'Employed Private','Employed Government','Self-Earning Individual',
    'OFW Land-Based','OFW Sea-Based','Lifetime Member',
    'Senior Citizen','Indigent/Sponsored'
  ) NULL DEFAULT NULL,
  -- CF3-only
  MODIFY COLUMN `lmp`               DATE NULL DEFAULT NULL,
  MODIFY COLUMN `delivery_date`     DATE NULL DEFAULT NULL,
  MODIFY COLUMN `manner_of_delivery` ENUM(
    'Normal Spontaneous Delivery (NSD)','Caesarean Section (CS)',
    'Vacuum Extraction','Forceps Delivery','Breech Delivery'
  ) NULL DEFAULT NULL,
  MODIFY COLUMN `fetal_outcome` ENUM('Live Birth','Stillbirth','Abortion','Ectopic Pregnancy') NULL DEFAULT NULL,
  MODIFY COLUMN `birth_weight`  VARCHAR(20) NULL DEFAULT NULL;
