-- 03_seed_contexts.sql
-- Load ALL *_contexts.csv into contexts via a staging table.
-- Expected CSV headers (case-sensitive):
--   Course Code, Assessment Type, Context ID, Context Text

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

DROP TABLE IF EXISTS staging_contexts;
CREATE TEMP TABLE staging_contexts (
  course_code       TEXT,
  assessment_type   TEXT,
  context_local_id  TEXT,
  context_text      TEXT
);

-- Concatenate all *_contexts.csv found in db-init/data
COPY staging_contexts (course_code, assessment_type, context_local_id, context_text)
FROM PROGRAM 'bash -lc ''cat /db-seed/data/*_contexts.csv 2>/dev/null || true''' WITH (FORMAT csv, HEADER true);

-- Merge into contexts
INSERT INTO contexts (assessment_id, course_id, context_local_id, context_text)
SELECT
  a.assessment_id,
  c.course_id,
  s.context_local_id,
  s.context_text
FROM staging_contexts s
JOIN courses c
  ON c.course_code = s.course_code
JOIN assessments a
  ON a.course_id = c.course_id
 AND a.assessment_type = s.assessment_type
ON CONFLICT (assessment_id, context_local_id)
DO UPDATE SET
  context_text = EXCLUDED.context_text;

DROP TABLE IF EXISTS staging_contexts;
