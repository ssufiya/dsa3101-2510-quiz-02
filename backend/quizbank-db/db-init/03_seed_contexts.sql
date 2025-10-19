DO $$
DECLARE
  csv_file TEXT;
  v_course_code TEXT;
  v_acad_year TEXT;
  v_assessment_type TEXT;
  v_course_id INTEGER;
BEGIN
  -- temp table matches headers in *_context.csv
  CREATE TEMP TABLE tmp_contexts (
    "Context ID" TEXT,
    "Context Text" TEXT,
    "Context Attachment" TEXT
  );

  -- iterate data files
  FOR csv_file IN
    SELECT * FROM pg_ls_dir('/docker-entrypoint-initdb.d/data') AS t(filename)
    WHERE filename LIKE '%_context.csv'
  LOOP
    RAISE NOTICE 'Loading file: %', csv_file;

    -- Parse filename → course_code, acad_year, assessment_type
    IF csv_file LIKE 'IND%' OR csv_file LIKE 'ST%' THEN
      v_course_code    := split_part(csv_file, '_', 1);
      v_assessment_type:= split_part(csv_file, '_', 2);
      v_acad_year      := NULL;
    ELSE
      v_course_code    := split_part(csv_file, '_', 1);
      v_acad_year      := split_part(csv_file, '_', 3);
      v_assessment_type:= replace(split_part(csv_file, '_', 4), '_context.csv', '');
    END IF;

    -- Ensure course row exists
    EXECUTE format(
      'INSERT INTO courses(course_code, course_name)
       VALUES (%L,%L) ON CONFLICT(course_code) DO NOTHING;',
      v_course_code, v_course_code
    );

    SELECT course_id INTO v_course_id
    FROM courses WHERE course_code = v_course_code;

    -- Load CSV
    EXECUTE format(
      'COPY tmp_contexts FROM %L WITH (FORMAT csv, HEADER true)',
      '/docker-entrypoint-initdb.d/data/' || csv_file
    );

    -- Insert contexts (one row per local id + text)
    INSERT INTO contexts (
      course_id, assessment_type, assessment_acadyear,
      context_local_id, context_text, context_attachment
    )
    SELECT
      v_course_id,
      v_assessment_type,
      v_acad_year,
      NULLIF(TRIM(t."Context ID"), ''),
      NULLIF(TRIM(t."Context Text"), ''),
      NULLIF(TRIM(t."Context Attachment"), '')
    FROM tmp_contexts t
    WHERE NULLIF(TRIM(t."Context Text"), '') IS NOT NULL
    ON CONFLICT ON CONSTRAINT uq_contexts_key DO NOTHING;

    -- Handle multiple attachments per context safely
    INSERT INTO attachments (context_id, attachment_name, attachment_type)
    SELECT DISTINCT
    c.context_id,
    TRIM(BOTH '"' FROM att) AS attachment_name,
    CASE
        WHEN att ILIKE '%.r' THEN 'r'
        WHEN att ~* '\.(png|jpg|jpeg|gif|svg|webp)$' THEN 'image'
        WHEN att ~* '\.(pdf|md|txt)$' THEN 'doc'
        ELSE 'other'
    END AS attachment_type
    FROM tmp_contexts t
    JOIN contexts c
    ON c.course_id = v_course_id
    AND c.assessment_type = v_assessment_type
    AND COALESCE(c.assessment_acadyear, '') = COALESCE(v_acad_year, '')
    AND c.context_local_id = t."Context ID"
    CROSS JOIN LATERAL unnest(
    regexp_split_to_array(
        regexp_replace(COALESCE(t."Context Attachment", ''), '\s*,\s*', ',', 'g'),
        ','
    )
    ) AS att
    WHERE TRIM(att) <> ''
    ON CONFLICT (context_id, attachment_name) DO NOTHING;


    TRUNCATE tmp_contexts;
  END LOOP;

  DROP TABLE tmp_contexts;
END $$;
