-- =====================================================================
-- 008_maternity_diagnoses.sql
-- Maternity diagnoses and reasons for admission, for the offline AI's
-- pattern recognition (Ocr_module/paddle_assist.py).
--
-- Research design §3.4.2.3 and the Reference Resources paragraph of
-- §3.4.1 call for "a list of maternity-related diagnoses and their
-- common abbreviations". This is that list, loaded into the same
-- `ocr_known_entries` vocabulary the AI already uses, so a garbled
-- PaddleOCR reading of a diagnosis column can be matched against what
-- staff actually write instead of being guessed at.
--
-- These are seeded as `starter` rows. Every review the staff confirm
-- adds to the same table as `learned`, so the clinic's own wording
-- takes over with use. Re-running this file is safe: existing rows are
-- left untouched.
--
-- Apply with:
--   mariadb -u root -h 127.0.0.1 pclaimassist_db < 008_maternity_diagnoses.sql
-- =====================================================================

-- --------------------------------------------------------------------
-- Admitting diagnosis / reason for admission
-- --------------------------------------------------------------------
INSERT IGNORE INTO `ocr_known_entries`
  (`category`, `entry_type`, `entry_key`, `entry_text`, `source`)
VALUES
  ('ADMITTING DIAGNOSIS','value','pregnancy uterine full term cephalic in labor','PREGNANCY UTERINE FULL TERM, CEPHALIC IN LABOR','starter'),
  ('ADMITTING DIAGNOSIS','value','pregnancy uterine full term cephalic not in labor','PREGNANCY UTERINE FULL TERM, CEPHALIC NOT IN LABOR','starter'),
  ('ADMITTING DIAGNOSIS','value','g1p0 pregnancy uterine full term in labor','G1P0 PREGNANCY UTERINE FULL TERM IN LABOR','starter'),
  ('ADMITTING DIAGNOSIS','value','term pregnancy in active labor','TERM PREGNANCY IN ACTIVE LABOR','starter'),
  ('ADMITTING DIAGNOSIS','value','term pregnancy in latent labor','TERM PREGNANCY IN LATENT LABOR','starter'),
  ('ADMITTING DIAGNOSIS','value','preterm labor','PRETERM LABOR','starter'),
  ('ADMITTING DIAGNOSIS','value','premature rupture of membranes','PREMATURE RUPTURE OF MEMBRANES','starter'),
  ('ADMITTING DIAGNOSIS','value','threatened abortion','THREATENED ABORTION','starter'),
  ('ADMITTING DIAGNOSIS','value','incomplete abortion','INCOMPLETE ABORTION','starter'),
  ('ADMITTING DIAGNOSIS','value','hyperemesis gravidarum','HYPEREMESIS GRAVIDARUM','starter'),
  ('ADMITTING DIAGNOSIS','value','urinary tract infection in pregnancy','URINARY TRACT INFECTION IN PREGNANCY','starter'),
  ('ADMITTING DIAGNOSIS','value','anemia in pregnancy','ANEMIA IN PREGNANCY','starter'),
  ('ADMITTING DIAGNOSIS','value','gestational hypertension','GESTATIONAL HYPERTENSION','starter'),
  ('ADMITTING DIAGNOSIS','value','preeclampsia','PREECLAMPSIA','starter'),
  ('ADMITTING DIAGNOSIS','value','severe preeclampsia','SEVERE PREECLAMPSIA','starter'),
  ('ADMITTING DIAGNOSIS','value','gestational diabetes mellitus','GESTATIONAL DIABETES MELLITUS','starter'),
  ('ADMITTING DIAGNOSIS','value','oligohydramnios','OLIGOHYDRAMNIOS','starter'),
  ('ADMITTING DIAGNOSIS','value','breech presentation','BREECH PRESENTATION','starter'),
  ('ADMITTING DIAGNOSIS','value','postdate pregnancy','POSTDATE PREGNANCY','starter'),
  ('ADMITTING DIAGNOSIS','value','for prenatal check up','FOR PRENATAL CHECK-UP','starter');

-- --------------------------------------------------------------------
-- Final / discharge diagnosis, including the referral wording this
-- clinic uses on CF2.
-- --------------------------------------------------------------------
INSERT IGNORE INTO `ocr_known_entries`
  (`category`, `entry_type`, `entry_key`, `entry_text`, `source`)
VALUES
  ('FINAL DIAGNOSIS','value','normal spontaneous delivery','NORMAL SPONTANEOUS DELIVERY','starter'),
  ('FINAL DIAGNOSIS','value','normal spontaneous delivery live birth','NORMAL SPONTANEOUS DELIVERY, LIVE BIRTH','starter'),
  ('FINAL DIAGNOSIS','value','delivered live term baby boy','DELIVERED LIVE TERM BABY BOY','starter'),
  ('FINAL DIAGNOSIS','value','delivered live term baby girl','DELIVERED LIVE TERM BABY GIRL','starter'),
  ('FINAL DIAGNOSIS','value','referral due to complication during 1st stage of labor','REFERRAL DUE TO COMPLICATION DURING 1ST STAGE OF LABOR','starter'),
  ('FINAL DIAGNOSIS','value','referral due to cephalopelvic disproportion','REFERRAL DUE TO CEPHALOPELVIC DISPROPORTION','starter'),
  ('FINAL DIAGNOSIS','value','referred to higher center','REFERRED TO HIGHER CENTER','starter'),
  ('FINAL DIAGNOSIS','value','cesarean section','CESAREAN SECTION','starter'),
  ('FINAL DIAGNOSIS','value','retained placenta','RETAINED PLACENTA','starter'),
  ('FINAL DIAGNOSIS','value','postpartum hemorrhage','POSTPARTUM HEMORRHAGE','starter'),
  ('FINAL DIAGNOSIS','value','perineal laceration 1st degree','PERINEAL LACERATION, 1ST DEGREE','starter'),
  ('FINAL DIAGNOSIS','value','perineal laceration 2nd degree','PERINEAL LACERATION, 2ND DEGREE','starter'),
  ('FINAL DIAGNOSIS','value','prolonged second stage of labor','PROLONGED SECOND STAGE OF LABOR','starter'),
  ('FINAL DIAGNOSIS','value','fetal distress','FETAL DISTRESS','starter'),
  ('FINAL DIAGNOSIS','value','completed abortion','COMPLETED ABORTION','starter');

-- --------------------------------------------------------------------
-- Abbreviations staff write in the logbook. `word` entries let the AI
-- recognise a single token inside a longer, part-garbled reading.
-- --------------------------------------------------------------------
INSERT IGNORE INTO `ocr_known_entries`
  (`category`, `entry_type`, `entry_key`, `entry_text`, `source`)
VALUES
  ('ADMITTING DIAGNOSIS','word','putifl','PUTIFL','starter'),
  ('ADMITTING DIAGNOSIS','word','aog','AOG','starter'),
  ('ADMITTING DIAGNOSIS','word','gravida','GRAVIDA','starter'),
  ('ADMITTING DIAGNOSIS','word','para','PARA','starter'),
  ('ADMITTING DIAGNOSIS','word','cephalic','CEPHALIC','starter'),
  ('ADMITTING DIAGNOSIS','word','prom','PROM','starter'),
  ('ADMITTING DIAGNOSIS','word','pih','PIH','starter'),
  ('ADMITTING DIAGNOSIS','word','uti','UTI','starter'),
  ('FINAL DIAGNOSIS','word','nsd','NSD','starter'),
  ('FINAL DIAGNOSIS','word','nsdl','NSDL','starter'),
  ('FINAL DIAGNOSIS','word','cs','CS','starter'),
  ('FINAL DIAGNOSIS','word','pph','PPH','starter'),
  ('FINAL DIAGNOSIS','word','cpd','CPD','starter'),
  ('FINAL DIAGNOSIS','word','lbw','LBW','starter');
