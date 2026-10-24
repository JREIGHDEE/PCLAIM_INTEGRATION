-- =====================================================================
-- 009_clinic_provider_rep.sql
-- The clinic's authorized HCI representative and attending health care
-- professional, entered once.
--
-- CSF Part V (Provider Information and Certification) asks for the name
-- and official capacity/designation of the clinic's authorized
-- representative. That is the same person on every claim, so it is kept
-- with the other clinic details (005_clinic_settings.sql) and filled in
-- on each claim instead of being retyped. So is the attending health care
-- professional who certifies CF4 Part VII (also the first professional on
-- CSF Part III and CF2): their name and accreditation number.
--
-- Apply with:
--   mariadb -u root -h 127.0.0.1 pclaimassist_db < 009_clinic_provider_rep.sql
-- =====================================================================

ALTER TABLE `clinic_settings`
  ADD COLUMN IF NOT EXISTS `provider_rep_name` VARCHAR(255) NOT NULL DEFAULT ''
    AFTER `hci_zip`,
  ADD COLUMN IF NOT EXISTS `provider_capacity` VARCHAR(255) NOT NULL DEFAULT ''
    AFTER `provider_rep_name`,
  ADD COLUMN IF NOT EXISTS `attending_name` VARCHAR(255) NOT NULL DEFAULT ''
    AFTER `provider_capacity`,
  ADD COLUMN IF NOT EXISTS `attending_pan` VARCHAR(20) NOT NULL DEFAULT ''
    AFTER `attending_name`;
