-- =====================================================================
-- Migration 003: per-row OCR review data on `case_sessions`.
--
-- Why: uploading a logbook scan now creates one case session per patient
-- row (Ocr_module/logbook_pipeline.py). Each OCR'd field carries its raw
-- text, PaddleOCR confidence, confidence routing status, cell crop and the
-- claim field it maps to - none of which had a column before. Rows from
-- one upload also need to be grouped, and a session created by OCR must
-- not become a claim until a person has reviewed it.
--
--   ocr_data      - JSON: {"image_quality": {...IQ-01...}, "fields": [...]}
--   upload_id     - groups the sessions created from one uploaded scan
--   logbook_row   - the row's position on the scanned page (0-based)
--   review_status - 'pending' until the reviewer submits the session;
--                   existing rows (entered through the manual review UI)
--                   default to 'reviewed', so they behave exactly as before.
--
-- Purely additive - no existing column or row is changed.
--
-- Apply this once against an existing pclaimassist_db (as root, e.g. in
-- phpMyAdmin's SQL tab). A fresh database created from the current
-- database/schema.sql already has these columns.
-- =====================================================================

USE `pclaimassist_db`;

ALTER TABLE `case_sessions`
  ADD COLUMN `ocr_data`      JSON              NULL DEFAULT NULL AFTER `reviewed_values`,
  ADD COLUMN `upload_id`     VARCHAR(64)       NULL DEFAULT NULL AFTER `source_document`,
  ADD COLUMN `logbook_row`   SMALLINT UNSIGNED NULL DEFAULT NULL AFTER `upload_id`,
  ADD COLUMN `review_status` ENUM('pending','reviewed') NOT NULL DEFAULT 'reviewed' AFTER `logbook_row`,
  ADD KEY `idx_case_sessions_upload_id` (`upload_id`);
