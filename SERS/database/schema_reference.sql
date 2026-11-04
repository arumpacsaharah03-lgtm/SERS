-- Reference schema for the domain tables created by Django migrations.
-- Use `python manage.py migrate` instead of executing this file directly.

CREATE TABLE Departments (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  code VARCHAR(20) NOT NULL UNIQUE,
  created_at DATETIME(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE Programs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  department_id BIGINT NOT NULL,
  name VARCHAR(150) NOT NULL,
  code VARCHAR(30) NOT NULL UNIQUE,
  created_at DATETIME(6) NOT NULL,
  CONSTRAINT Programs_department_fk FOREIGN KEY (department_id)
    REFERENCES Departments(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE Students (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL UNIQUE,
  student_id VARCHAR(30) NOT NULL UNIQUE,
  middle_name VARCHAR(100) NULL,
  department_id BIGINT NOT NULL,
  program_id BIGINT NOT NULL,
  year_level SMALLINT UNSIGNED NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  CONSTRAINT Students_user_fk FOREIGN KEY (user_id)
    REFERENCES auth_user(id) ON DELETE CASCADE,
  CONSTRAINT Students_department_fk FOREIGN KEY (department_id)
    REFERENCES Departments(id) ON DELETE RESTRICT,
  CONSTRAINT Students_program_fk FOREIGN KEY (program_id)
    REFERENCES Programs(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE Events (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  description LONGTEXT NOT NULL,
  category VARCHAR(30) NOT NULL,
  event_date DATE NOT NULL,
  start_time TIME(6) NOT NULL,
  end_time TIME(6) NOT NULL,
  venue VARCHAR(200) NOT NULL,
  registration_deadline DATETIME(6) NOT NULL,
  maximum_participants INT UNSIGNED NOT NULL,
  image VARCHAR(100) NULL,
  status VARCHAR(20) NOT NULL,
  created_by_id BIGINT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  CONSTRAINT Events_created_by_fk FOREIGN KEY (created_by_id)
    REFERENCES auth_user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE Registrations (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  student_id BIGINT NOT NULL,
  event_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'Pending',
  reviewed_by_id BIGINT NULL,
  reviewed_at DATETIME(6) NULL,
  rejection_reason VARCHAR(255) NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  CONSTRAINT Registrations_student_fk FOREIGN KEY (student_id)
    REFERENCES Students(id) ON DELETE CASCADE,
  CONSTRAINT Registrations_event_fk FOREIGN KEY (event_id)
    REFERENCES Events(id) ON DELETE CASCADE,
  CONSTRAINT Registrations_reviewer_fk FOREIGN KEY (reviewed_by_id)
    REFERENCES auth_user(id) ON DELETE SET NULL,
  CONSTRAINT unique_student_event UNIQUE (student_id, event_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
