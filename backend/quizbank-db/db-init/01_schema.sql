BEGIN;

-- ================================================================
-- Drop existing tables (in dependency-safe order)
-- ================================================================
DROP TABLE IF EXISTS attachments CASCADE;
DROP TABLE IF EXISTS questions CASCADE;
DROP TABLE IF EXISTS contexts CASCADE;
DROP TABLE IF EXISTS assessments CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ================================================================
-- USERS TABLE (not yet used, but kept for completeness)
-- ================================================================
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username TEXT,
    password_hash TEXT NOT NULL
);

-- ================================================================
-- COURSES TABLE
-- ================================================================
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_code TEXT UNIQUE NOT NULL,
    course_name TEXT
);

-- ================================================================
-- ASSESSMENTS TABLE
-- ================================================================
CREATE TABLE assessments (
    assessment_id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    assessment_type TEXT NOT NULL,
    assessment_acadyear TEXT,
    assessment_semester TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    CONSTRAINT uq_assessments_unique UNIQUE (course_id, assessment_type, assessment_acadyear, assessment_semester)
);

-- ================================================================
-- CONTEXTS TABLE
-- Each context belongs to a course and an assessment
-- ================================================================
CREATE TABLE contexts (
    context_id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    context_local_id TEXT,
    context_text TEXT,
    context_attachment TEXT,
    CONSTRAINT uq_contexts_key UNIQUE (assessment_id, context_local_id)
);

-- ================================================================
-- QUESTIONS TABLE
-- Each question belongs to a course, assessment, and optionally a context
-- ================================================================

CREATE TABLE questions (
    question_id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(course_id) ON DELETE CASCADE,
    assessment_id INTEGER REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    context_id INTEGER REFERENCES contexts(context_id) ON DELETE SET NULL,

    question_number TEXT,
    sub_question_number TEXT,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50),
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    option_e TEXT,
    correct_answer TEXT,
    explanation TEXT,
    points NUMERIC DEFAULT 1.0,
    difficulty VARCHAR(50),
    concepts TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    version_number INTEGER DEFAULT 1,
    previous_version_id INTEGER REFERENCES questions(question_id) DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT uq_questions_dedupe UNIQUE (course_id, assessment_id, question_text)
);


-- ================================================================
-- ATTACHMENTS TABLE
-- Stores all files associated with contexts or questions
-- ================================================================
CREATE TABLE attachments (
    attachment_id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES contexts(context_id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questions(question_id) ON DELETE CASCADE,
    attachment_name VARCHAR(255),
    attachment_type VARCHAR(255),
    CONSTRAINT uq_attachments_question_file UNIQUE (question_id, attachment_name),
    CONSTRAINT uq_attachments_context_file UNIQUE (context_id, attachment_name)
);

-- ================================================================
-- Helpful indexes
-- ================================================================
CREATE INDEX idx_questions_context_id ON questions(context_id);
CREATE INDEX idx_questions_assessment_id ON questions(assessment_id);
CREATE INDEX idx_contexts_assessment_id ON contexts(assessment_id);
CREATE INDEX idx_contexts_course_id ON contexts(course_id);
CREATE INDEX idx_attachments_question_id ON attachments(question_id);
CREATE INDEX idx_attachments_context_id ON attachments(context_id);

COMMIT;
