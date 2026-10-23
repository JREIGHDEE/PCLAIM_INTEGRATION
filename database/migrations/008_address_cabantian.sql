-- =====================================================================
-- 008_address_cabantian.sql
-- "Cabantian" as a starter address word, for the offline AI's pattern
-- recognition (Ocr_module/paddle_assist.py, ocr_known_entries - see 007).
--
-- The clinic is in Cabantian, Davao City, so most addresses in the logbook
-- end in it. "Davao" and "City" are already starter words (007); this adds
-- the barangay. A reading close to it ("CABANTlAN", "Cabantain") in an
-- address cell PaddleOCR was unsure about is then suggested as "Cabantian".
-- It is only a suggestion: the field stays "please check" for staff to
-- confirm, a reading PaddleOCR was sure of is never touched, and a word not
-- close to it is left as read.
--
-- To stop it being suggested, set is_active = 0 in phpMyAdmin.
--
-- Apply with:
--   mariadb -u root -h 127.0.0.1 pclaimassist_db < 008_address_cabantian.sql
-- (or paste it into phpMyAdmin's SQL tab)
-- =====================================================================

-- Already learned from reviews: its counts are kept, and as a starter it
-- also gets the starter weight, so it stays known whatever reviews undo.
INSERT INTO `ocr_known_entries` (`category`, `entry_type`, `entry_key`, `entry_text`, `source`)
VALUES ('ADDRESS', 'word', 'CABANTIAN', 'Cabantian', 'starter')
ON DUPLICATE KEY UPDATE `source` = 'starter';
