-- 04_seed_questions.sql
-- Load ALL *_questions.csv into questions with proper version linking.
-- Expected CSV headers (case-sensitive):
-- Course Code, Assessment Type, Context ID, Question Text, Question Type,
-- Option A, Option B, Option C, Option D, Option E,
-- Correct Answer, Explanation, Points, Difficulty, Concepts, Version Number

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- 1) Stage CSV
DROP TABLE IF EXISTS staging_questions;
CREATE TEMP TABLE staging_questions (
  course_code       TEXT,
  assessment_type   TEXT,
  context_local_id  TEXT,
  question_text     TEXT,
  question_type     TEXT,
  option_a          TEXT,
  option_b          TEXT,
  option_c          TEXT,
  option_d          TEXT,
  option_e          TEXT,
  correct_answer    TEXT,
  explanation       TEXT,
  points            TEXT,
  difficulty        TEXT,
  concepts          TEXT,
  version_number    INTEGER
);

COPY staging_questions (
  course_code, assessment_type, context_local_id, question_text, question_type,
  option_a, option_b, option_c, option_d, option_e,
  correct_answer, explanation, points, difficulty, concepts, version_number
)
FROM PROGRAM 'bash -lc ''cat /db-seed/data/*_questions.csv 2>/dev/null || true''' WITH (FORMAT csv, HEADER true);

-- 2) Insert/Update rows (without previous/original yet)
INSERT INTO questions (
  assessment_id, course_id, context_id,
  question_text, question_type,
  option_a, option_b, option_c, option_d, option_e,
  correct_answer, explanation, points, difficulty, concepts,
  version_number, is_latest
)
SELECT
  a.assessment_id,
  c.course_id,
  ctx.context_id,
  sq.question_text,
  sq.question_type,
  NULLIF(sq.option_a, ''),
  NULLIF(sq.option_b, ''),
  NULLIF(sq.option_c, ''),
  NULLIF(sq.option_d, ''),
  NULLIF(sq.option_e, ''),
  NULLIF(sq.correct_answer, ''),
  NULLIF(sq.explanation, ''),
  NULLIF(sq.points, '')::NUMERIC(4,1),
  NULLIF(sq.difficulty, ''),
  NULLIF(sq.concepts, ''),
  COALESCE(sq.version_number, 1),
  TRUE
FROM staging_questions sq
JOIN courses c
  ON c.course_code = sq.course_code
JOIN assessments a
  ON a.course_id = c.course_id
 AND a.assessment_type = sq.assessment_type
LEFT JOIN contexts ctx
  ON ctx.assessment_id = a.assessment_id
 AND ctx.context_local_id = sq.context_local_id
ON CONFLICT (course_id, assessment_id, question_text)
DO UPDATE SET
  question_type  = EXCLUDED.question_type,
  option_a       = EXCLUDED.option_a,
  option_b       = EXCLUDED.option_b,
  option_c       = EXCLUDED.option_c,
  option_d       = EXCLUDED.option_d,
  option_e       = EXCLUDED.option_e,
  correct_answer = EXCLUDED.correct_answer,
  explanation    = EXCLUDED.explanation,
  points         = EXCLUDED.points,
  difficulty     = EXCLUDED.difficulty,
  concepts       = EXCLUDED.concepts,
  context_id     = EXCLUDED.context_id,
  version_number = EXCLUDED.version_number,
  is_latest      = TRUE;

-- For any older versions of the same natural key, mark is_latest = FALSE
WITH maxv AS (
  SELECT
    course_id, assessment_id, question_text,
    MAX(version_number) AS max_version
  FROM questions
  GROUP BY 1,2,3
)
UPDATE questions q
SET is_latest = (q.version_number = m.max_version)
FROM maxv m
WHERE q.course_id = m.course_id
  AND q.assessment_id = m.assessment_id
  AND q.question_text = m.question_text;

-- 3) Link original_id = first version (min version_number for the same key)
WITH firsts AS (
  SELECT DISTINCT ON (course_id, assessment_id, question_text)
         course_id, assessment_id, question_text,
         question_id AS original_qid,
         version_number
  FROM questions
  ORDER BY course_id, assessment_id, question_text, version_number ASC, question_id ASC
)
UPDATE questions q
SET original_id = f.original_qid
FROM firsts f
WHERE q.course_id = f.course_id
  AND q.assessment_id = f.assessment_id
  AND q.question_text = f.question_text
  AND q.original_id IS DISTINCT FROM f.original_qid;

-- 4) Link previous_version_id to the immediate prior version (version_number - 1)
WITH prevs AS (
  SELECT q.course_id, q.assessment_id, q.question_text, q.version_number,
         q.question_id AS qid
  FROM questions q
),
pairs AS (
  SELECT cur.course_id, cur.assessment_id, cur.question_text,
         cur.qid AS current_qid,
         prev.qid AS prev_qid
  FROM prevs cur
  JOIN prevs prev
    ON prev.course_id = cur.course_id
   AND prev.assessment_id = cur.assessment_id
   AND prev.question_text = cur.question_text
   AND prev.version_number = cur.version_number - 1
)
UPDATE questions q
SET previous_version_id = p.prev_qid
FROM pairs p
WHERE q.question_id = p.current_qid
  AND (q.previous_version_id IS DISTINCT FROM p.prev_qid OR q.previous_version_id IS NULL);

-- Clean up
DROP TABLE IF EXISTS staging_questions;
