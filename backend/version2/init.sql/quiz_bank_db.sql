
-- users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(225) NOT NULL,
    role VARCHAR(25) DEFAULT 'instructor',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- courses table
CREATE TABLE IF NOT EXISTS courses (
    course_id SERIAL PRIMARY KEY,
    course_code VARCHAR(10) UNIQUE NOT NULL,
    course_name VARCHAR(255) NOT NULL
);


-- assessments table 
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(course_id),
    assessment_type VARCHAR(50),
    assessment_acadyear VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id)
);

-- contexts table 
CREATE TABLE IF NOT EXISTS contexts (
    context_id SERIAL PRIMARY KEY,
    context_text TEXT,
    context_attachment VARCHAR(500)
);

-- attachments table (for images/files)
CREATE TABLE IF NOT EXISTS attachments (
    attachment_id SERIAL PRIMARY KEY,
    attachment_name VARCHAR(255),
    attachment_type VARCHAR(50),
    context_id INTEGER REFERENCES contexts(context_id),
    question_id INTEGER  -- Will add FK constraint after questions table
);

-- questions table
CREATE TABLE IF NOT EXISTS questions (
    question_id SERIAL PRIMARY KEY,
    assessment_id INTEGER REFERENCES assessments(assessment_id),
    course_id INTEGER REFERENCES courses(course_id),
    context_id INTEGER REFERENCES contexts(context_id),
    attachment_id INTEGER REFERENCES attachments(attachment_id),
    question_text TEXT NOT NULL,
    question_type VARCHAR(50),
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    option_e TEXT,
    correct_answer VARCHAR(10),
    difficulty VARCHAR(20),
    concepts VARCHAR(255),
    created_by INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version_number INTEGER DEFAULT 1,
    previous_version_id INTEGER REFERENCES questions(question_id)
);

-- Add foreign key constraint to attachments now that questions exists
ALTER TABLE attachments 
ADD CONSTRAINT fk_attachments_question 
FOREIGN KEY (question_id) REFERENCES questions(question_id);
