-- 01_schema.sql
-- Core QuizBank schema (PostgreSQL)

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- ---------- users ----------
CREATE TABLE IF NOT EXISTS users (
  user_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username       VARCHAR(128) NOT NULL UNIQUE,
  password_hash  VARCHAR(256) NOT NULL
);

-- ---------- courses ----------
CREATE TABLE IF NOT EXISTS courses (
  course_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  course_code  VARCHAR(32)  NOT NULL UNIQUE,
  course_name  VARCHAR(256) NOT NULL
);

-- ---------- assessments ----------
CREATE TABLE IF NOT EXISTS assessments (
  assessment_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  course_id            BIGINT       NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
  assessment_type      VARCHAR(64)  NOT NULL,
  assessment_acadyear  VARCHAR(32),
  assessment_semester  VARCHAR(32),
  created_at           TIMESTAMPTZ  DEFAULT NOW(),
  created_by           BIGINT       REFERENCES users(user_id),

  CONSTRAINT uq_assessment UNIQUE (course_id, assessment_type, assessment_acadyear, assessment_semester)
);

-- ---------- contexts ----------
CREATE TABLE IF NOT EXISTS contexts (
  context_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  assessment_id    BIGINT      NOT NULL REFERENCES assessments(assessment_id) ON DELETE CASCADE,
  course_id        BIGINT      NOT NULL REFERENCES courses(course_id)     ON DELETE CASCADE,
  context_local_id VARCHAR(64) NOT NULL,
  context_text     TEXT        NOT NULL,

  CONSTRAINT uq_context UNIQUE (assessment_id, context_local_id)
);

-- ---------- context_attachments ----------
CREATE TABLE IF NOT EXISTS context_attachments (
  context_attachment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  context_id      BIGINT       NOT NULL REFERENCES contexts(context_id) ON DELETE CASCADE,
  attachment_name VARCHAR(256) NOT NULL,
  attachment_url  VARCHAR(1024),
  CONSTRAINT uq_context_attachment UNIQUE (context_id, attachment_name)
);

-- ---------- questions ----------
CREATE TABLE IF NOT EXISTS questions (
  question_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  assessment_id    BIGINT      NOT NULL REFERENCES assessments(assessment_id) ON DELETE CASCADE,
  course_id        BIGINT      NOT NULL REFERENCES courses(course_id)     ON DELETE CASCADE,
  context_id       BIGINT      REFERENCES contexts(context_id) ON DELETE SET NULL,

  question_number      INTEGER,
  sub_question_number  INTEGER,

  question_text    TEXT        NOT NULL,
  question_type    VARCHAR(64),

  option_a         TEXT,
  option_b         TEXT,
  option_c         TEXT,
  option_d         TEXT,
  option_e         TEXT,

  correct_answer   TEXT,
  explanation      TEXT,
  points           DECIMAL(4,1),
  difficulty       VARCHAR(32),
  concepts         TEXT,

  created_by       BIGINT       REFERENCES users(user_id),
  created_at       TIMESTAMPTZ  DEFAULT NOW(),

  -- versioning (links set after bulk insert in 04_seed_questions.sql)
  version_number       INTEGER      NOT NULL DEFAULT 1,
  previous_version_id  BIGINT,
  original_id          BIGINT,
  is_latest            BOOLEAN      NOT NULL DEFAULT TRUE,

  -- natural de-dup key (matches your updater)
  CONSTRAINT uq_question UNIQUE (course_id, assessment_id, question_text)
);

-- self-referential FKs for versioning
ALTER TABLE questions
  ADD CONSTRAINT fk_questions_previous
  FOREIGN KEY (previous_version_id)
  REFERENCES questions(question_id)
  ON DELETE SET NULL
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE questions
  ADD CONSTRAINT fk_questions_original
  FOREIGN KEY (original_id)
  REFERENCES questions(question_id)
  ON DELETE SET NULL
  DEFERRABLE INITIALLY DEFERRED;

-- safety checks
ALTER TABLE questions
  ADD CONSTRAINT chk_prev_not_self
  CHECK (previous_version_id IS NULL OR previous_version_id <> question_id);

ALTER TABLE questions
  ADD CONSTRAINT chk_orig_not_self
  CHECK (original_id IS NULL OR original_id <> question_id);

-- ---------- question_attachments ----------
CREATE TABLE IF NOT EXISTS question_attachments (
  question_attachment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question_id    BIGINT       NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
  attachment_name VARCHAR(256) NOT NULL,
  attachment_url  VARCHAR(1024),
  CONSTRAINT uq_question_attachment UNIQUE (question_id, attachment_name)
);

-- helpful indexes
CREATE INDEX IF NOT EXISTS idx_assessments_course     ON assessments(course_id);
CREATE INDEX IF NOT EXISTS idx_contexts_assessment    ON contexts(assessment_id);
CREATE INDEX IF NOT EXISTS idx_questions_assessment   ON questions(assessment_id);
CREATE INDEX IF NOT EXISTS idx_questions_context      ON questions(context_id);
CREATE INDEX IF NOT EXISTS idx_questions_previous     ON questions(previous_version_id);
CREATE INDEX IF NOT EXISTS idx_questions_original     ON questions(original_id);
