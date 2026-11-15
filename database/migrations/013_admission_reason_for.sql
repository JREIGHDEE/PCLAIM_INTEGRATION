-- =====================================================================
-- 013_admission_reason_for.sql
-- Reason for admission of a well baby and a postpartum visit, as the
-- clinic's logbook writes them: "FOR WELL BABY CARE", "FOR POSTPARTUM
-- VISIT" (the research answer key), like every other visit ("FOR PSI
-- INSERTION", "FOR PILLS REFILL"). Migration 012 started them without
-- the "FOR". The discharge diagnosis stays WELL BABY CARE / POSTPARTUM
-- VISIT (PClaimAssist/js/app.js dischargeFromAdmission).
--
-- Only a pattern still worded as 012 left it is changed, so a wording
-- staff set on the Admission patterns page is kept. Safe to run twice.
-- Apply with:
--   mariadb -u root -h 127.0.0.1 pclaimassist_db < 013_admission_reason_for.sql
-- (or paste it into phpMyAdmin's SQL tab, as root)
-- =====================================================================

UPDATE `admission_patterns` SET `reason` = 'FOR WELL BABY CARE'
 WHERE `name` = 'Well baby care' AND `reason` = 'WELL BABY CARE';

UPDATE `admission_patterns` SET `reason` = 'FOR POSTPARTUM VISIT'
 WHERE `name` = 'Postpartum visit' AND `reason` = 'POSTPARTUM VISIT';
