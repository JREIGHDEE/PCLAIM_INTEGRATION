-- =====================================================================
-- 011_encrypt_patient_details.sql
-- Room for encrypted patient details (adviser's revision S4: "sensitive
-- patient data encrypted").
--
-- Ocr_module/field_crypto.py now encrypts the PhilHealth PINs, phone
-- numbers, email and street-level address before they are written, and
-- what is typed on the forms (claims.form_values, already LONGTEXT). An
-- encrypted value ("enc1:" + a Fernet token) is several times longer
-- than the text it holds - a 14-character PIN becomes about 125
-- characters - so these columns become TEXT. How much plain text each
-- may hold is unchanged: the application keeps the old limits
-- (field_crypto.PLAINTEXT_MAX).
--
-- Nullable with no default, as before. Rows saved earlier stay readable
-- (a value without "enc1:" is read as it is) and are encrypted the next
-- time they are saved.
--
-- Safe to run twice. Apply with:
--   mariadb -u root -h 127.0.0.1 pclaimassist_db < 011_encrypt_patient_details.sql
-- (or paste it into phpMyAdmin's SQL tab, as root)
-- =====================================================================

ALTER TABLE `patients`
  MODIFY COLUMN `pin`     TEXT NULL DEFAULT NULL,
  MODIFY COLUMN `address` TEXT NULL DEFAULT NULL;

ALTER TABLE `claims`
  MODIFY COLUMN `member_pin`     TEXT NULL DEFAULT NULL,
  MODIFY COLUMN `employer_phone` TEXT NULL DEFAULT NULL,
  MODIFY COLUMN `mobile`         TEXT NULL DEFAULT NULL,
  MODIFY COLUMN `home_phone`     TEXT NULL DEFAULT NULL,
  MODIFY COLUMN `email`          TEXT NULL DEFAULT NULL,
  MODIFY COLUMN `addr_unit`      TEXT NULL DEFAULT NULL,
  MODIFY COLUMN `addr_building`  TEXT NULL DEFAULT NULL,
  MODIFY COLUMN `addr_lot`       TEXT NULL DEFAULT NULL,
  MODIFY COLUMN `addr_street`    TEXT NULL DEFAULT NULL;
