-- =====================================================================
-- Migration 002: add `patients.address`.
--
-- Why: the OCR logbook has an ADDRESS column (config.py TRAINING_CATEGORIES)
-- that was already being captured during OCR review and saved into
-- case_sessions.reviewed_values, but the OCR-to-claim bridge
-- (philhealth/case_bridge.py) had nowhere to put it afterwards - `patients`
-- had no address column at all, so that OCR output was silently dropped
-- every time a claim was generated. This adds the missing destination
-- column so the bridge can carry it through instead of discarding it.
--
-- Nullable, no default, purely additive - does not affect any existing row
-- or any other column.
--
-- Apply this once against an existing pclaimassist_db that was created
-- before this column was added. A fresh database created from the current
-- database/schema.sql already has this column and does not need this file.
-- =====================================================================

USE `pclaimassist_db`;

ALTER TABLE `patients`
  ADD COLUMN `address` VARCHAR(255) NULL DEFAULT NULL AFTER `pin`;
