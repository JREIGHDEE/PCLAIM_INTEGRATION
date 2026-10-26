-- =====================================================================
-- 010_claim_mother_baby.sql
-- A newborn's claim linked to its mother's, and what staff type on the
-- forms kept with each claim.
--
-- A maternity clinic files a claim for the mother and another for her
-- baby. Most of the baby's claim repeats the mother's: the PhilHealth
-- member (usually the mother herself), the home address and contact,
-- the member's profile and employer. Staff tick "Copy the mother's
-- details" on the baby's claim instead of typing them again.
--
--   patient_role     'mother' / 'baby' / 'other' as chosen by staff; NULL
--                    means not chosen, and the role is worked out from the
--                    logbook entry (philhealth/mother_baby.py).
--   mother_claim_id  the mother's claim a baby's claim copies from.
--   form_values      everything typed on the forms for this claim (JSON,
--                    form key -> value), saved as staff type. The logbook
--                    only fills a few fields; without this the rest - the
--                    mother's PIN, phone, civil status - would be gone by
--                    the time her baby's entry is opened.
--
-- Apply with:
--   mariadb -u root -h 127.0.0.1 pclaimassist_db < 010_claim_mother_baby.sql
-- =====================================================================

ALTER TABLE `claims`
  ADD COLUMN IF NOT EXISTS `patient_role` ENUM('mother','baby','other') NULL DEFAULT NULL
    AFTER `status`,
  ADD COLUMN IF NOT EXISTS `mother_claim_id` INT UNSIGNED NULL DEFAULT NULL
    AFTER `patient_role`,
  ADD COLUMN IF NOT EXISTS `form_values` LONGTEXT NULL DEFAULT NULL
    AFTER `mother_claim_id`;

ALTER TABLE `claims`
  ADD CONSTRAINT `fk_claims_mother_claim`
    FOREIGN KEY IF NOT EXISTS (`mother_claim_id`) REFERENCES `claims` (`id`)
    ON DELETE SET NULL;
