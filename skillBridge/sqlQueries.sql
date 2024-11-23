-- Create the database and use it
CREATE DATABASE skillBridge;
USE skillBridge;

-- Create the Users table
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Create the Skills table
CREATE TABLE Skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50)
);

-- Create the User_Skills table
CREATE TABLE User_Skills (
    user_skill_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_id INT NOT NULL,
    proficiency INT NOT NULL,
    is_mentor BOOLEAN DEFAULT FALSE,
    last_assessed DATETIME,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Create the Profiles table
CREATE TABLE Profiles (
    profile_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    experience_years INT,
    learning_goals TEXT,
    areas_of_improvement TEXT,
    primary_skill INT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (primary_skill) REFERENCES Skills(skill_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Create the Assessments table
CREATE TABLE Assessments (
    assessment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_id INT NOT NULL,
    score INT NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Create the Mentorships table
CREATE TABLE Mentorships (
    mentorship_id INT AUTO_INCREMENT PRIMARY KEY,
    mentor_id INT NOT NULL,
    mentee_id INT NOT NULL,
    skill_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (mentor_id) REFERENCES Users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (mentee_id) REFERENCES Users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Create the Certifications table
CREATE TABLE Certifications (
    certification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_id INT NOT NULL,
    mentor_id INT,
    certificate_name VARCHAR(255) NOT NULL,
    issued_by VARCHAR(255),
    issue_date DATETIME,
    expiry_date DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (mentor_id) REFERENCES Users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE Mentor_Requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    mentee_id INT NOT NULL,
    mentor_id INT NOT NULL,
    skill_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    certificate_url VARCHAR(255) DEFAULT NULL,
    status ENUM('Pending', 'Approved', 'Denied',"Ongoing","Completed") DEFAULT 'Pending',
    created_at DATETIME DEFAULT '0000-00-00 00:00:00',
    updated_at DATETIME,
    FOREIGN KEY (mentee_id) REFERENCES Users(user_id),
    FOREIGN KEY (mentor_id) REFERENCES Users(user_id),
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id)
);


INSERT INTO Skills (name, description, category) VALUES
('HTML', 'Standard markup language for creating web pages.', 'Web Development'),
('WordPress', 'Open-source content management system for creating websites and blogs.', 'Web Development'),
('Python', 'High-level programming language for general-purpose programming.', 'Programming'),
('MySQL', 'Relational database management system for structured data.', 'Database'),
('React', 'JavaScript library for building user interfaces.', 'Web Development'),
('Terraform', 'Infrastructure-as-code tool for building and managing cloud resources.', 'Cloud Computing'),
('DevOps', 'Cultural and technical practices for automating software development.', 'DevOps'),
('BASH', 'Unix shell and command language used for scripting.', 'Scripting'),
('Linux', 'Open-source operating system widely used in servers and systems.', 'Operating Systems'),
('PHP', 'Popular server-side scripting language for web development.', 'Web Development'),
('PostgreSQL', 'Advanced open-source relational database management system.', 'Database'),
('Docker', 'Tool for creating and managing containers.', 'DevOps'),
('JavaScript', 'Popular scripting language for web development.', 'Web Development'),
('Ansible', 'Tool for configuration management and automation.', 'DevOps'),
('Java', 'Object-oriented programming language widely used in enterprise applications.', 'Programming'),
('Kubernetes', 'System for automating deployment, scaling, and managing containers.', 'DevOps'),
('AWS', 'Cloud computing platform offering a wide range of services.', 'Cloud Computing'),
('Azure', 'Cloud platform for building, managing, and deploying applications.', 'Cloud Computing'),
('Git', 'Version control system for tracking code changes.', 'Version Control'),
('Machine Learning', 'Field of AI focused on building systems that learn from data.', 'AI/ML'),
('Deep Learning', 'Subset of machine learning focused on neural networks.', 'AI/ML'),
('Cybersecurity', 'Practices for protecting systems and networks from attacks.', 'Security');

CREATE TABLE SkillQuestions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    option_a VARCHAR(255) NOT NULL,
    option_b VARCHAR(255) NOT NULL,
    option_c VARCHAR(255) NOT NULL,
    option_d VARCHAR(255) NOT NULL,
    correct_option CHAR(1) NOT NULL,
    FOREIGN KEY (skill_name) REFERENCES Skills(name) ON DELETE CASCADE
);


CREATE TABLE SkillAssessments (
    assessment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_name VARCHAR(255) NOT NULL,
    score INT NOT NULL,
    grade VARCHAR(50) NOT NULL,
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (skill_name) REFERENCES Skills(name)
);
