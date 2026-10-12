-- =====================================================================
-- 004_users_auth.sql
-- User accounts for authentication and role-based access control.
--
-- Research design §3.4.2.7 ("user accounts for role-based access
-- control") and §3.8 Security Measures ("user authentication and
-- role-based access control before pilot testing").
--
-- Passwords are NEVER stored. `password_hash` holds a bcrypt hash, which
-- is one-way: it can verify a password but cannot reveal it, so a copy of
-- this table does not expose anyone's credentials.
--
-- Roles (one per user, matching the clinic staff described in §3.3.1):
--   encoder - midwife or administrative clerk. Prepares claims: OCR
--             review, form data entry, validation, PDF generation.
--   admin   - clinic administrator. Everything an encoder can do, plus
--             managing user accounts and clinic-wide settings.
--
-- Apply with:
--   mariadb -u root -h 127.0.0.1 pclaimassist_db < 004_users_auth.sql
-- =====================================================================

CREATE TABLE IF NOT EXISTS `users` (
  `id`             INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- Login identifier. Stored lower-cased by the application so that
  -- "Maria@clinic.ph" and "maria@clinic.ph" are the same account.
  `email`          VARCHAR(190) NOT NULL,

  -- bcrypt hash (60 chars today; VARCHAR(255) leaves room for a future
  -- algorithm without another migration).
  `password_hash`  VARCHAR(255) NOT NULL,

  `full_name`      VARCHAR(150) NOT NULL,
  `role`           ENUM('encoder','admin') NOT NULL DEFAULT 'encoder',

  -- Soft disable: an account can be switched off without deleting it,
  -- so its audit trail in case_sessions/claims stays intact.
  `is_active`      TINYINT(1) NOT NULL DEFAULT 1,

  -- Lets staff see "last signed in" and supports the pilot's usage notes.
  `last_login_at`  DATETIME NULL DEFAULT NULL,

  `created_at`     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                     ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`),
  KEY `idx_users_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
