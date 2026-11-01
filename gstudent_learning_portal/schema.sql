CREATE DATABASE IF NOT EXISTS gstudent_portal;
USE gstudent_portal;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reg_no VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student','admin') NOT NULL DEFAULT 'student',
    status ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- After registering your first account, promote it to admin using:
-- UPDATE users SET role='admin', status='approved' WHERE reg_no='YOUR_REGISTRATION_NO';
