DO $$
DECLARE
  csv_file        TEXT;
  v_course_code   TEXT;
  v_acad_year     TEXT;
  v_assessment_type TEXT;
  v_semester        TEXT; 
  v_course_id     INTEGER;
  v_assessment_id INTEGER;
BEGIN
  CREATE TEMP TABLE tmp_contexts (
    "Context ID"         TEXT,
    "Context Text"       TEXT,
    "Context Attachment" TEXT
  );

  FOR csv_file IN
    SELECT * FROM pg_ls_dir('/docker-entrypoint-initdb.d/data') AS t(filename)
    WHERE filename LIKE '%_context.csv'
  LOOP
    RAISE NOTICE 'Loading file: %', csv_file;

    -- Parse filename pattern
    IF csv_file LIKE 'IND%' OR csv_file LIKE 'ST%' THEN
      -- e.g., IND5003_Supervised_context.csv
      v_course_code     := split_part(csv_file, '_', 1);
      v_assessment_type := split_part(csv_file, '_', 2);
      v_acad_year       := NULL;
      v_semester        := NULL;
    ELSE
    -- e.g., DSA1101_Sem1_2425_Quiz6_questions.csv
      v_course_code     := split_part(csv_file, '_', 1);

      IF csv_file LIKE '%Sem%' THEN
        v_semester := split_part(csv_file, '_', 2);
        v_acad_year           := split_part(csv_file, '_', 3);
        v_assessment_type     := split_part(csv_file, '_', 4);
      ELSE
        v_semester := NULL;
        v_acad_year           := NULL;
        v_assessment_type := split_part(csv_file, '_', 2);
      END IF;

    END IF;

    -- Ensure course
    EXECUTE format(
      'INSERT INTO courses(course_code, course_name)
       VALUES (%L,%L) ON CONFLICT(course_code) DO NOTHING;',
      v_course_code, v_course_code
    );
    SELECT course_id INTO v_course_id FROM courses WHERE course_code = v_course_code;

    -- Ensure assessment (created_by null for now)
    EXECUTE format(
      $sql$
      INSERT INTO assessments(course_id, assessment_type, assessment_acadyear, assessment_semester)
      VALUES (%s, %L, %L, %L)
      ON CONFLICT DO NOTHING;
      $sql$,
      v_course_id, v_assessment_type, v_acad_year, v_semester
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
      'COPY tmp_contexts FROM %L WITH (FORMAT csv, HEADER true)',
      '/docker-entrypoint-initdb.d/data/' || csv_file
    );

    -- Insert contexts (now keyed by assessment_id + local id)
    INSERT INTO contexts(
      assessment_id, course_id,
      context_local_id, context_text, context_attachment
    )
    SELECT
      v_assessment_id, v_course_id,
      t."Context ID", t."Context Text", t."Context Attachment"
    FROM tmp_contexts t
    WHERE NULLIF(TRIM(t."Context Text"), '') IS NOT NULL
    ON CONFLICT ON CONSTRAINT uq_contexts_key DO NOTHING;

    -- Context-level attachments (split commas; supports .r, .csv, images, docs)
    INSERT INTO attachments (context_id, attachment_name, attachment_type)
    SELECT DISTINCT
      c.context_id,
      TRIM(att) AS attachment_name,
      CASE
        WHEN att ~* '\.(r)$'                          THEN 'r'
        WHEN att ~* '\.(csv)$'                        THEN 'csv'
        WHEN att ~* '\.(png|jpg|jpeg|gif|svg|webp)$'  THEN 'image'
        WHEN att ~* '\.(pdf|md|txt)$'                 THEN 'doc'
        ELSE 'other'
      END AS attachment_type
    FROM tmp_contexts t
    JOIN contexts c
      ON c.assessment_id = v_assessment_id
     AND c.context_local_id = t."Context ID"
    CROSS JOIN LATERAL regexp_split_to_table(COALESCE(t."Context Attachment", ''), '\s*,\s*') AS att
    WHERE TRIM(att) <> ''
    ON CONFLICT ON CONSTRAINT uq_attachments_context_file DO NOTHING;

    TRUNCATE tmp_contexts;
  END LOOP;

  DROP TABLE tmp_contexts;
END $$;
