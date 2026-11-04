-- =====================================================================
-- The research database: only the two reference tables the correction
-- model reads, seeded with the system's own starter rows - never the
-- clinic's database (its learned rows came from test-set pages).
--
-- Easiest: run  Ocr_module\venv\Scripts\python.exe -m research_tests.setup.import_seed
-- which does everything below and checks the result.
--
-- By hand (phpMyAdmin, SQL tab, as root):
--   1. run this file;
--   2. run database/migrations/006_ocr_correction_patterns.sql,
--      007_ocr_known_entries.sql and 008_address_cabantian.sql
--      with pclaimassist_research selected (not pclaimassist_db);
--   3. if Ocr_module/.env uses an app account (DB_USER) other than root:
--      GRANT SELECT ON pclaimassist_research.* TO '<DB_USER>'@'localhost';
--      GRANT SELECT ON pclaimassist_research.* TO '<DB_USER>'@'127.0.0.1';
-- Safe to run twice.
-- =====================================================================
CREATE DATABASE IF NOT EXISTS `pclaimassist_research`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
