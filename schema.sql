-- Create database with UTF8MB4 support
CREATE DATABASE IF NOT EXISTS college_events CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE college_events;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    location VARCHAR(200) NOT NULL,
    capacity INT NOT NULL,
    image_url VARCHAR(255),
    status ENUM('draft', 'published', 'cancelled') DEFAULT 'published',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Event registrations table
CREATE TABLE IF NOT EXISTS event_registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    user_id INT NOT NULL,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'confirmed', 'cancelled') DEFAULT 'confirmed',
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY unique_registration (event_id, user_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Event requests table
CREATE TABLE IF NOT EXISTS event_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    proposed_date DATE NOT NULL,
    proposed_time TIME NOT NULL,
    location VARCHAR(200) NOT NULL,
    capacity INT NOT NULL,
    requested_by INT NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    admin_remarks TEXT,
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requested_by) REFERENCES users(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, role) 
VALUES ('admin', 'admin@example.com', 
        'pbkdf2:sha256:600000$dxoMVtxlGo8hYLaE$5b74c76b79d76b2605e0b32357c89e6e76adcf4a2f3439b4293fcd3345d62286',
        'admin')
ON DUPLICATE KEY UPDATE id=id;

-- Insert some sample events
INSERT INTO events (title, description, date, time, location, capacity, status, created_by)
VALUES 
    ('Rongoli', 
     'colors of joy',
     '2024-03-15',
     '15:30:00',
     'hyderabad',
     200,
     'published',
     1),
    ('ganesh',
     'ganesh',
     '2024-03-20',
     '16:00:00',
     'JNTU Sulthanpur',
     300,
     'published',
     1);

-- Update the event_requests table
ALTER TABLE event_requests ADD COLUMN image_url VARCHAR(255);

-- Update the events table
ALTER TABLE events ADD COLUMN image_url VARCHAR(255); 