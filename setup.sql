-- SQL script to set up test users and root admin
-- Run this with: mysql -u wm -p wm123!@# wm < setup.sql

-- Clear existing users (optional - comment out if you want to keep existing data)
-- DELETE FROM user;

-- Insert a root admin user (password: admin123)
-- SHA256 hash of "admin123" = 0c33f88b65fea2988e34c20b8efc81c111ce579052081803d1b5aade66e4b08a
INSERT INTO user (username, pwhash, introduction, rating, type, deleted) 
VALUES ('admin', '0c33f88b65fea2988e34c20b8efc81c111ce579052081803d1b5aade66e4b08a', 'Administrator', 0, 'root', 0)
ON DUPLICATE KEY UPDATE id=id;

-- Insert a normal test user (password: test123456)
-- SHA256 hash of "test123456" = 589cff1767de5e24db2cf088f34f1fcd8a46c6d9b5aba27d6d31a38c5c5f2e7f
INSERT INTO user (username, pwhash, introduction, rating, type, deleted) 
VALUES ('testuser', '589cff1767de5e24db2cf088f34f1fcd8a46c6d9b5aba27d6d31a38c5c5f2e7f', 'Test User', 0, 'normal', 0)
ON DUPLICATE KEY UPDATE id=id;

SELECT * FROM user;
