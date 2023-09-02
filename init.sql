SET global general_log = 1;
SET global log_output = 'table';
GRANT ALL PRIVILEGES ON `test_${DB_NAME}`.* TO '${DB_USER}'@'%';
GRANT ALL PRIVILEGES ON `${DB_NAME}`.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;
