CREATE TABLE IF NOT EXISTS student_metrics (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL,
    attendance_rate REAL NOT NULL,
    submission_delay REAL NOT NULL,
    grades REAL NOT NULL,
    activity_score REAL NOT NULL,
    engagement_decline REAL NOT NULL DEFAULT 0,
    stress_label VARCHAR(30) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_student_metrics_student_id
    ON student_metrics(student_id);
