-- =====================================================================
-- 005_clinic_settings.sql
-- The clinic's own details, entered once and reused on every claim.
--
-- Research design Table 3.1 lists "Clinic name, accreditation number, and
-- address" (used by CF2, CF3 and CF4) with the source "System settings
-- (entered once)". Until now these were retyped on each form, which is the
-- repeated transcription the study set out to remove (§I).
--
-- Deliberately a single-row table: one installation serves one clinic
-- (§3.4.2.7, the database runs on that clinic's own local server). The
-- CHECK constraint keeps it that way rather than relying on convention.
--
-- Apply with:
--   mariadb -u root -h 127.0.0.1 pclaimassist_db < 005_clinic_settings.sql
-- =====================================================================

CREATE TABLE IF NOT EXISTS `clinic_settings` (
  -- Pinned to 1 so there can only ever be one clinic record.
  `id`                INT UNSIGNED NOT NULL DEFAULT 1,

  `hci_name`          VARCHAR(255) NOT NULL DEFAULT '',
  `hci_pan`           VARCHAR(20)  NOT NULL DEFAULT '',

  -- Address split to match the printed CF4 address boxes.
  `hci_bldg`          VARCHAR(255) NOT NULL DEFAULT '',
  `hci_street`        VARCHAR(255) NOT NULL DEFAULT '',
  `hci_city`          VARCHAR(100) NOT NULL DEFAULT '',
  `hci_province`      VARCHAR(100) NOT NULL DEFAULT '',
  `hci_zip`           VARCHAR(10)  NOT NULL DEFAULT '',

  -- Who last changed these, for the clinic's own accountability.
  `updated_by`        INT UNSIGNED NULL DEFAULT NULL,
  `updated_at`        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  CONSTRAINT `chk_clinic_settings_single_row` CHECK (`id` = 1),
  CONSTRAINT `fk_clinic_settings_user` FOREIGN KEY (`updated_by`)
    REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Seed the single row so the app can always UPDATE rather than branch on
-- "does a row exist yet".
INSERT IGNORE INTO `clinic_settings` (`id`) VALUES (1);
