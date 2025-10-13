-- =============================================================
-- DSDS Quizbank Schema (PostgreSQL Compatible, circular FKs handled)
-- =============================================================

BEGIN;

-- Drop tables if you want a clean rerun (comment these if you already have data)
DROP TABLE IF EXISTS attachments CASCADE;
DROP TABLE IF EXISTS questions CASCADE;
DROP TABLE IF EXISTS contexts CASCADE;
DROP TABLE IF EXISTS assessments CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ===================== USERS =====================
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

-- ===================== COURSES =====================
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    course_name VARCHAR(255) NOT NULL
);

-- ===================== ASSESSMENTS =====================
CREATE TABLE assessments (
    assessment_id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    assessment_type VARCHAR(100) NOT NULL,
    assessment_acadyear VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL
);

-- ===================== CONTEXTS =====================
CREATE TABLE contexts (
    context_id SERIAL PRIMARY KEY,
    context_text TEXT,
    context_attachment VARCHAR(255)
);

-- ===================== QUESTIONS =====================
-- Note: no FK to attachments yet (to avoid circular reference)
CREATE TABLE questions (
    question_id SERIAL PRIMARY KEY,
    assessment_id INTEGER REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(course_id) ON DELETE CASCADE,
    context_id INTEGER REFERENCES contexts(context_id) ON DELETE SET NULL,
    attachment_id INTEGER,  -- FK added later
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    option_e TEXT,
    correct_answer VARCHAR(255),
    difficulty VARCHAR(50),
    concepts VARCHAR(255),
    created_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version_number INTEGER DEFAULT 1,
    previous_version_id INTEGER  -- self-FK added later
);

-- ===================== ATTACHMENTS =====================
-- Note: no FK to questions yet (to avoid circular reference)
CREATE TABLE attachments (
    attachment_id SERIAL PRIMARY KEY,
    attachment_name VARCHAR(255),
    attachment_type VARCHAR(100),
    context_id INTEGER REFERENCES contexts(context_id) ON DELETE CASCADE,
    question_id INTEGER  -- FK added later
);

-- ===================== ADD THE CROSS/SELF FKs =====================

-- If constraints exist from a previous run, drop them so the script is re-runnable
ALTER TABLE IF EXISTS questions   DROP CONSTRAINT IF EXISTS fk_questions_attachment;
ALTER TABLE IF EXISTS attachments DROP CONSTRAINT IF EXISTS fk_attachments_question;
ALTER TABLE IF EXISTS questions   DROP CONSTRAINT IF EXISTS fk_questions_previous_version;

-- Now add them
ALTER TABLE questions
  ADD CONSTRAINT fk_questions_attachment
  FOREIGN KEY (attachment_id)
  REFERENCES attachments(attachment_id)
  ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE attachments
  ADD CONSTRAINT fk_attachments_question
  FOREIGN KEY (question_id)
  REFERENCES questions(question_id)
  ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE questions
  ADD CONSTRAINT fk_questions_previous_version
  FOREIGN KEY (previous_version_id)
  REFERENCES questions(question_id)
  ON UPDATE CASCADE ON DELETE SET NULL
  DEFERRABLE INITIALLY DEFERRED;

-- ===================== Indexes =====================
CREATE INDEX IF NOT EXISTS idx_questions_assessment_id ON questions(assessment_id);
CREATE INDEX IF NOT EXISTS idx_questions_course_id     ON questions(course_id);
CREATE INDEX IF NOT EXISTS idx_assessments_course_id   ON assessments(course_id);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty    ON questions(difficulty);

COMMIT;
