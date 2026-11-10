-- =============================================================================
-- Database Schema & Initial Seed Data: AntiBurnout WebPBL
-- Engine: SQLite / MySQL Compatible DDL
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Tabel: users (Akun Administrator & Operator Sistem)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'admin',
    division VARCHAR(50) DEFAULT 'Pusat Riset PBL',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Akun Administrator Default (Password: admin123)
INSERT INTO users (id, username, email, password_hash, full_name, role, division, created_at)
VALUES (
    1,
    'admin',
    'admin@antiburnout.com',
    'scrypt:32768:8:1$FBPkEwix6Lyvkouj$acb5251b8785dde178ad49df1296b99c0b936e4afc1198be55c40a0b9db20756ae0ba9a97f03005d02c9ffa2ab6702ee061210abf752384f8f4067f18230b472',
    'Administrator PBL',
    'admin',
    'Pusat Riset PBL',
    CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 2. Tabel: assessments (Data Primer Responden & Hasil Evaluasi Burnout)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    work_hours REAL NOT NULL,
    sleep_hours REAL NOT NULL,
    stress_level INTEGER NOT NULL,
    workload_feeling INTEGER NOT NULL,
    physical_fatigue INTEGER NOT NULL,
    notes TEXT,
    burnout_score REAL,
    burnout_level VARCHAR(50),
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample Data Primer Responden
INSERT INTO assessments (id, full_name, role, work_hours, sleep_hours, stress_level, workload_feeling, physical_fatigue, notes, burnout_score, burnout_level, recommendation, created_at)
VALUES 
(1, 'Budi Santoso', 'Teknologi / IT', 9.0, 6.0, 4, 4, 4, 'Uji coba Clean Architecture', 66.2, 'Sedang (Moderate Risk)', 'Mulai terindikasi kelelahan kerja. Disarankan untuk mengambil jeda dan mengatur beban tugas.', CURRENT_TIMESTAMP),
(2, 'Ahmad Fauzi', 'Kesehatan / Medis', 10.0, 5.0, 5, 5, 5, 'Shift malam berturut-turut', 79.2, 'Tinggi (High Risk / Burnout)', 'Tingkat stres dan beban kerja tinggi terdeteksi. Segera lakukan pemulihan dan konsultasi.', CURRENT_TIMESTAMP),
(3, 'Karyawan-A01', 'Pendidikan / Pengajar', 8.0, 7.0, 2, 3, 2, 'Data kuesioner fisik lembar #4', 46.3, 'Sedang (Moderate Risk)', 'Mulai terindikasi kelelahan kerja. Disarankan untuk mengambil jeda dan mengatur beban tugas.', CURRENT_TIMESTAMP);
