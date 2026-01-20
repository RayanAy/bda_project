-- SCRIPT DE CRÉATION DE LA BASE DE DONNÉES BDDA
-- Exécuter : mysql -u root -p < schema.sql

DROP DATABASE IF EXISTS BDDA;
CREATE DATABASE BDDA CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE BDDA;

-- Table départements
CREATE TABLE departements (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table formations
CREATE TABLE formations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(150) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    dept_id INT NOT NULL,
    nb_modules INT DEFAULT 6,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departements(id) ON DELETE CASCADE
);

-- Table professeurs
CREATE TABLE professeurs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    dept_id INT NOT NULL,
    specialite VARCHAR(255),
    grade ENUM('PROF', 'MC', 'VAC') DEFAULT 'MC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departements(id) ON DELETE CASCADE
);

-- Table modules
CREATE TABLE modules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(150) NOT NULL,
    credits INT DEFAULT 6,
    formation_id INT NOT NULL,
    prof_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (formation_id) REFERENCES formations(id) ON DELETE CASCADE,
    FOREIGN KEY (prof_id) REFERENCES professeurs(id) ON DELETE SET NULL
);

-- Table étudiants
CREATE TABLE etudiants (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    formation_id INT NOT NULL,
    promo YEAR NOT NULL,
    matricule VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (formation_id) REFERENCES formations(id) ON DELETE CASCADE
);

-- Table salles d'examen
CREATE TABLE lieu_examen (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    capacite INT NOT NULL,
    type ENUM('AMPHI', 'SALLE', 'LABO') NOT NULL,
    batiment VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table inscriptions
CREATE TABLE inscriptions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    etudiant_id INT NOT NULL,
    module_id INT NOT NULL,
    annee_academique YEAR NOT NULL,
    semestre ENUM('S1', 'S2') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE,
    UNIQUE KEY uq_inscription (etudiant_id, module_id, annee_academique)
);

-- Table examens
CREATE TABLE examens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    module_id INT NOT NULL,
    prof_id INT NOT NULL,
    salle_id INT NOT NULL,
    date_heure DATETIME NOT NULL,
    duree_minutes INT NOT NULL,
    surveillants_requis INT DEFAULT 1,
    statut ENUM('PLANIFIE', 'CONFIRME', 'ANNULE') DEFAULT 'PLANIFIE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE,
    FOREIGN KEY (prof_id) REFERENCES professeurs(id) ON DELETE CASCADE,
    FOREIGN KEY (salle_id) REFERENCES lieu_examen(id) ON DELETE CASCADE
);

-- Table conflits
CREATE TABLE conflits (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    type ENUM('ETUDIANT', 'PROFESSEUR', 'SALLE', 'CAPACITE') NOT NULL,
    examen_id INT NOT NULL,
    description TEXT NOT NULL,
    severite ENUM('CRITIQUE', 'MAJEUR', 'MINEUR') DEFAULT 'MAJEUR',
    statut ENUM('DETECTE', 'RESOLU', 'IGNORE') DEFAULT 'DETECTE',
    date_detection TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_resolution TIMESTAMP NULL,
    FOREIGN KEY (examen_id) REFERENCES examens(id) ON DELETE CASCADE
);

-- =====================================================
-- INSERTION DES DONNÉES DE TEST
-- =====================================================

-- Insertion des départements
INSERT INTO departements (nom, code) VALUES
('Informatique', 'INFO'),
('Mathématiques', 'MATH'),
('Physique', 'PHYS'),
('Chimie', 'CHIM'),
('Biologie', 'BIO'),
('Économie', 'ECO'),
('Droit', 'DROIT');

-- Insertion des formations
INSERT INTO formations (nom, code, dept_id, nb_modules) VALUES
('Licence Informatique', 'LIC-INFO-1', 1, 6),
('Master Informatique', 'MAST-INFO-1', 1, 8),
('Licence Mathématiques', 'LIC-MATH-1', 2, 6),
('Master Mathématiques', 'MAST-MATH-1', 2, 8),
('Licence Physique', 'LIC-PHYS-1', 3, 6);

-- Insertion des professeurs
INSERT INTO professeurs (nom, prenom, dept_id, specialite, grade) VALUES
('Dupont', 'Jean', 1, 'Base de données', 'PROF'),
('Martin', 'Sophie', 1, 'Intelligence Artificielle', 'MC'),
('Bernard', 'Pierre', 1, 'Réseaux', 'PROF'),
('Petit', 'Marie', 2, 'Analyse', 'PROF'),
('Roux', 'Claude', 2, 'Algèbre', 'MC'),
('Leroy', 'Thomas', 3, 'Mécanique', 'PROF'),
('Moreau', 'Julie', 4, 'Chimie organique', 'MC');

-- Insertion des modules
INSERT INTO modules (nom, credits, formation_id, prof_id) VALUES
('Base de données', 6, 1, 1),
('Programmation Python', 6, 1, 2),
('Algorithmique', 6, 1, 3),
('Réseaux informatiques', 6, 1, 3),
('Analyse mathématique', 6, 3, 4),
('Algèbre linéaire', 6, 3, 5),
('Mécanique classique', 6, 5, 6),
('Chimie générale', 6, 4, 7);

-- Insertion des étudiants (100 étudiants de test)
INSERT INTO etudiants (nom, prenom, formation_id, promo, matricule) VALUES
('Durand', 'Paul', 1, 2026, 'ETU001'),
('Leroy', 'Julie', 1, 2026, 'ETU002'),
('Moreau', 'Thomas', 1, 2026, 'ETU003'),
('Simon', 'Laura', 1, 2026, 'ETU004'),
('Laurent', 'Marc', 2, 2025, 'ETU005'),
('Michel', 'Emma', 2, 2025, 'ETU006'),
('Lefebvre', 'Nicolas', 3, 2026, 'ETU007'),
('Garcia', 'Ana', 3, 2026, 'ETU008'),
('Robert', 'Lucie', 3, 2026, 'ETU009'),
('Richard', 'David', 1, 2026, 'ETU010');

-- Insertion des salles d'examen
INSERT INTO lieu_examen (nom, capacite, type, batiment) VALUES
('Amphi A', 300, 'AMPHI', 'Bâtiment Principal'),
('Amphi B', 250, 'AMPHI', 'Bâtiment Principal'),
('Amphi C', 200, 'AMPHI', 'Bâtiment Sciences'),
('Salle 101', 30, 'SALLE', 'Bâtiment Informatique'),
('Salle 102', 25, 'SALLE', 'Bâtiment Informatique'),
('Salle 103', 20, 'SALLE', 'Bâtiment Informatique'),
('Labo Informatique 1', 40, 'LABO', 'Bâtiment Informatique'),
('Labo Informatique 2', 35, 'LABO', 'Bâtiment Informatique'),
('Salle 201', 50, 'SALLE', 'Bâtiment Mathématiques'),
('Salle 202', 45, 'SALLE', 'Bâtiment Mathématiques');

-- Insertion des inscriptions (chaque étudiant inscrit à 3-4 modules)
INSERT INTO inscriptions (etudiant_id, module_id, annee_academique, semestre) VALUES
(1, 1, 2025, 'S2'), (1, 2, 2025, 'S2'), (1, 3, 2025, 'S2'),
(2, 1, 2025, 'S2'), (2, 2, 2025, 'S2'), (2, 4, 2025, 'S2'),
(3, 2, 2025, 'S2'), (3, 3, 2025, 'S2'), (3, 4, 2025, 'S2'),
(4, 1, 2025, 'S2'), (4, 4, 2025, 'S2'),
(5, 5, 2025, 'S2'), (5, 6, 2025, 'S2'),
(6, 5, 2025, 'S2'), (6, 6, 2025, 'S2'),
(7, 7, 2025, 'S2'),
(8, 7, 2025, 'S2'),
(9, 8, 2025, 'S2'),
(10, 1, 2025, 'S2'), (10, 2, 2025, 'S2'), (10, 3, 2025, 'S2'), (10, 4, 2025, 'S2');

-- Insertion des examens
INSERT INTO examens (module_id, prof_id, salle_id, date_heure, duree_minutes, statut) VALUES
(1, 1, 1, '2025-06-10 08:00:00', 120, 'CONFIRME'),
(2, 2, 4, '2025-06-10 14:00:00', 120, 'CONFIRME'),
(3, 3, 1, '2025-06-11 10:30:00', 90, 'CONFIRME'),
(4, 3, 2, '2025-06-12 08:00:00', 120, 'CONFIRME'),
(5, 4, 9, '2025-06-12 14:00:00', 180, 'CONFIRME'),
(6, 5, 10, '2025-06-13 08:00:00', 120, 'CONFIRME'),
(7, 6, 3, '2025-06-13 14:00:00', 90, 'CONFIRME'),
(8, 7, 5, '2025-06-14 10:30:00', 120, 'CONFIRME');

-- Insertion de conflits de test
INSERT INTO conflits (type, examen_id, description, severite, statut) VALUES
('ETUDIANT', 1, 'Étudiant avec 2 examens le même jour', 'CRITIQUE', 'DETECTE'),
('CAPACITE', 2, 'Salle trop petite pour le nombre d\'étudiants', 'MAJEUR', 'DETECTE'),
('PROFESSEUR', 3, 'Professeur avec 3 examens le même jour', 'MAJEUR', 'RESOLU'),
('SALLE', 4, 'Deux examens programmés dans la même salle en même temps', 'CRITIQUE', 'DETECTE');

-- =====================================================
-- CRÉATION DE L'UTILISATEUR
-- =====================================================
CREATE USER IF NOT EXISTS 'bdda_user'@'localhost' IDENTIFIED BY 'Bdda@2026!';
GRANT ALL PRIVILEGES ON BDDA.* TO 'bdda_user'@'localhost';
FLUSH PRIVILEGES;

SELECT '✅ Base de données BDDA créée avec succès !' AS message;
SELECT '👨‍🎓 Étudiants:' AS table_name, COUNT(*) as count FROM etudiants
UNION ALL
SELECT '📝 Examens:', COUNT(*) FROM examens
UNION ALL
SELECT '👨‍🏫 Professeurs:', COUNT(*) FROM professeurs
UNION ALL
SELECT '🏫 Salles:', COUNT(*) FROM lieu_examen;