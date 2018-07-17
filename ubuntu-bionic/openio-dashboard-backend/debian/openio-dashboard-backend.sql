CREATE DATABASE openio_dashboard;
CREATE USER 'admin'@'localhost' IDENTIFIED BY '%PASSWORD%';
GRANT ALL PRIVILEGES on openio_dashboard.* to 'admin'@'localhost';
FLUSH PRIVILEGES;
