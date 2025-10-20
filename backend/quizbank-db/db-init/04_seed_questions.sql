DO $$
DECLARE
  csv_file          TEXT;
  v_course_code     TEXT;
  v_acad_year       TEXT;
  v_assessment_type TEXT;
  v_semester        TEXT;
  v_course_id       INTEGER;
  v_assessment_id   INTEGER;
BEGIN
  CREATE TEMP TABLE tmp_questions (
    "Context ID"          TEXT,
    "Question Number"     TEXT,
    "Sub-Question Number" TEXT,
    "Question Text"       TEXT,
    "Question Type"       TEXT,
    "Option A"            TEXT,
    "Option B"            TEXT,
    "Option C"            TEXT,
    "Option D"            TEXT,
    "Option E"            TEXT,
    "Correct Answer"      TEXT,
    "Explanation"         TEXT,
    "Points"              TEXT,
    "Difficulty"          TEXT,
    "Concepts"            TEXT,
    "Attachment"          TEXT
  );

  FOR csv_file IN
    SELECT * FROM pg_ls_dir('/docker-entrypoint-initdb.d/data') AS t(filename)
    WHERE filename LIKE '%_questions.csv'
  LOOP
    RAISE NOTICE 'Loading file: %', csv_file;

    -- Parse filename pattern
    IF csv_file LIKE 'IND%' OR csv_file LIKE 'ST%' THEN
      v_course_code     := split_part(csv_file, '_', 1);
      v_assessment_type := split_part(csv_file, '_', 2);
      v_acad_year       := NULL;
      v_semester        := NULL;
    ELSE
      v_course_code     := split_part(csv_file, '_', 1);
      v_semester        := split_part(csv_file, '_', 2);
      v_acad_year       := split_part(csv_file, '_', 3);
      v_assessment_type := split_part(csv_file, '_', 4);
    END IF;

    -- Ensure course
    EXECUTE format(
      'INSERT INTO courses(course_code, course_name)
       VALUES (%L,%L) ON CONFLICT(course_code) DO NOTHING;',
      v_course_code, v_course_code
    );
    SELECT course_id INTO v_course_id FROM courses WHERE course_code = v_course_code;

    -- Ensure assessment
    EXECUTE format(
      'INSERT INTO assessments(course_id, assessment_type, assessment_acadyear,assessment_semester)
       VALUES (%s,%L,%L,%L)
       ON CONFLICT (course_id, assessment_type, assessment_acadyear,assessment_semester) DO NOTHING;',
      v_course_id, v_assessment_type, v_acad_year,v_semester
    );
    SELECT assessment_id INTO v_assessment_id
      FROM assessments
     WHERE course_id = v_course_id
       AND assessment_type = v_assessment_type
       AND COALESCE(assessment_acadyear, '') = COALESCE(v_acad_year, '')
       AND COALESCE(assessment_semester, '') = COALESCE(v_semester, '')
     ORDER BY assessment_id DESC LIMIT 1;

    -- Load CSV
    EXECUTE format(
      'COPY tmp_questions FROM %L WITH (FORMAT csv, HEADER true)',
      '/docker-entrypoint-initdb.d/data/' || csv_file
    );

    -- Insert questions (include ones with no context)
    INSERT INTO questions (
      course_id, assessment_id, context_id,
      question_number, sub_question_number,
      question_text, question_type,
      option_a, option_b, option_c, option_d, option_e,
      correct_answer, explanation, points, difficulty, concepts
    )
    SELECT
      v_course_id,
      v_assessment_id,
      c.context_id,                        -- null if no matching context
      t."Question Number",
      t."Sub-Question Number",
      t."Question Text",
      t."Question Type",
      NULLIF(t."Option A", ''),
      NULLIF(t."Option B", ''),
      NULLIF(t."Option C", ''),
      NULLIF(t."Option D", ''),
      NULLIF(t."Option E", ''),
      NULLIF(t."Correct Answer", ''),
      NULLIF(t."Explanation", ''),
      COALESCE(NULLIF(t."Points", '')::NUMERIC, 1.0),
      LOWER(TRIM(NULLIF(t."Difficulty", ''))),
      NULLIF(t."Concepts", '')
    FROM tmp_questions t
    LEFT JOIN contexts c
      ON c.assessment_id   = v_assessment_id
     AND c.context_local_id = t."Context ID"
    WHERE NULLIF(TRIM(t."Question Text"), '') IS NOT NULL
    ON CONFLICT (course_id, assessment_id, question_text) DO NOTHING;

    -- Insert question-level attachments (comma-split; ignore explicit '!filename')
    INSERT INTO attachments (question_id, attachment_name, attachment_type)
    SELECT DISTINCT
      q.question_id,
      TRIM(att) AS attachment_name,
      CASE
        WHEN att ~* '\.(r)$'                          THEN 'r'
        WHEN att ~* '\.(csv)$'                        THEN 'csv'
        WHEN att ~* '\.(png|jpg|jpeg|gif|svg|webp)$'  THEN 'image'
        WHEN att ~* '\.(pdf|md|txt)$'                 THEN 'doc'
        ELSE 'other'
      END AS attachment_type
    FROM tmp_questions t
    JOIN questions q
      ON q.course_id = v_course_id
     AND q.assessment_id = v_assessment_id
     AND md5(q.question_text) = md5(t."Question Text")
    CROSS JOIN LATERAL regexp_split_to_table(COALESCE(t."Attachment", ''), '\s*,\s*') AS att
    WHERE TRIM(att) <> ''
      AND att NOT LIKE '!%'   -- explicit placement handled later by app layer if needed
    ON CONFLICT (question_id, attachment_name) DO NOTHING;

    TRUNCATE tmp_questions;
  END LOOP;

  DROP TABLE tmp_questions;
END $$;
