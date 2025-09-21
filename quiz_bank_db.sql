
-- users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(225) NOT NULL,
    role VARCHAR(25) DEFAULT 'instructor',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- courses table
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_code VARCHAR(10) UNIQUE NOT NULL,
    course_name VARCHAR(255) NOT NULL
);

-- tags table
CREATE TABLE tags (
    tag_id SERIAL PRIMARY KEY,
    tag_name VARCHAR(100) UNIQUE NOT NULL
);

-- questions table
CREATE TABLE questions (
    question_id SERIAL PRIMARY KEY,
    question_text TEXT NOT NULL,
    answer_text TEXT,
    question_type VARCHAR(50),
    difficulty_index DECIMAL(3,2),
    last_used TIMESTAMP NULL,
    course_id INT REFERENCES courses(course_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT REFERENCES users(user_id),
    updated_by INT REFERENCES users(user_id)
);

-- question_versions table
CREATE TABLE question_versions (
    version_id SERIAL PRIMARY KEY,
    question_id INT NOT NULL REFERENCES questions(question_id),
    version_number INT,
    question_text TEXT,
    answer_text TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INT REFERENCES users(user_id)
);

-- question_tags table
CREATE TABLE question_tags (
    question_id INT REFERENCES questions(question_id),
    tag_id INT REFERENCES tags(tag_id),
    PRIMARY KEY (question_id, tag_id)
);

-- datasets table
CREATE TABLE datasets (
    dataset_id SERIAL PRIMARY KEY,
    question_id INT REFERENCES questions(question_id),
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INT REFERENCES users(user_id)
);

-- assessments table
CREATE TABLE assessments (
    assessment_id SERIAL PRIMARY KEY,
    assessment_name VARCHAR(255) NOT NULL,
    course_id INT REFERENCES courses(course_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT REFERENCES users(user_id)
);

-- assessment_questions table
CREATE TABLE assessment_questions (
    assessment_id INT REFERENCES assessments(assessment_id),
    question_id INT REFERENCES questions(question_id),
    order_index INT,
    PRIMARY KEY (assessment_id, question_id)
);

-- question_usage table
CREATE TABLE question_usage (
    usage_id SERIAL PRIMARY KEY,
    question_id INT REFERENCES questions(question_id),
    assessment_id INT REFERENCES assessments(assessment_id),
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- performance table
CREATE TABLE performance (
    performance_id SERIAL PRIMARY KEY,
    question_id INT REFERENCES questions(question_id),
    assessment_id INT REFERENCES assessments(assessment_id),
    average_score DECIMAL(5,2),
    discriminant_index DECIMAL(5,2)
);
