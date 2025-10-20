-- Seed initial course list
COPY courses(course_code, course_name)
FROM '/docker-entrypoint-initdb.d/data/updated_nus_dsa_courses.csv'
CSV HEADER;
