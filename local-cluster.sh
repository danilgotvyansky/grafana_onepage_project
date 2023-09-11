#!/bin/bash

source ./.env

echo "Start time: $(date)"

echo "Compose Build"
BUILD_STATUS=$(docker-compose -f ${PWD}/compose.yaml build)
echo ${BUILD_STATUS}

echo "Start MariaDB1"

MariaDB1_UP_STATUS=$(docker-compose -f ${PWD}/compose.yaml up -d mariadb1)
sleep 5
echo ${MariaDB1_UP_STATUS}

echo "Grant slave for mariadb1 on mariadb2"
docker exec grafana_onepage_project-mariadb1-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -Nse "
GRANT REPLICATION SLAVE ON *.* TO '${DB_REPL2}'@'${DB_HOST2}' IDENTIFIED BY '${DB_REPL2_PASSWORD}';
FLUSH PRIVILEGES;
FLUSH TABLES WITH READ LOCK;
"

MASTER_STATUS1=$(docker exec grafana_onepage_project-mariadb1-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -Nse "SHOW MASTER STATUS")
FILE1=$(echo "${MASTER_STATUS1}" | awk '{ print $1 }')
POSITION1=$(echo "${MASTER_STATUS1}" | awk '{ print $2 }')
echo "Log File from Master Status: ${FILE1}"
echo "Log Position from Master Status: ${POSITION1}"

echo "Start MariaDB2"
MariaDB2_UP_STATUS=$(docker-compose -f ${PWD}/compose.yaml up -d mariadb2)
sleep 5
echo ${MariaDB2_UP_STATUS}

echo "Changing master on mariadb2 and start slave"
docker exec grafana_onepage_project-mariadb2-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -Nse "
CHANGE MASTER TO MASTER_HOST='${DB_HOST1}', MASTER_USER='${DB_REPL2}', MASTER_PASSWORD='${DB_REPL2_PASSWORD}', MASTER_PORT=3306, MASTER_LOG_FILE='${FILE1}', MASTER_LOG_POS=${POSITION1};
START SLAVE;
"

echo "Grant slave for mariadb2 on mariadb1"
docker exec grafana_onepage_project-mariadb2-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -Nse "
GRANT REPLICATION SLAVE ON *.* TO '${DB_REPL1}'@'${DB_HOST1}' IDENTIFIED BY '${DB_REPL1_PASSWORD}';
FLUSH PRIVILEGES;
FLUSH TABLES WITH READ LOCK;
"

MASTER_STATUS2=$(docker exec grafana_onepage_project-mariadb2-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -Nse "SHOW MASTER STATUS")
FILE2=$(echo "${MASTER_STATUS2}" | awk '{ print $1 }')
POSITION2=$(echo "${MASTER_STATUS2}" | awk '{ print $2 }')
echo "Log File from Master Status: ${FILE2}"
echo "Log Position from Master Status: ${POSITION2}"

echo "Changing master on mariadb1 and start slave"
docker exec grafana_onepage_project-mariadb1-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -Nse "
CHANGE MASTER TO MASTER_HOST='${DB_HOST2}', MASTER_USER='${DB_REPL1}', MASTER_PASSWORD='${DB_REPL1_PASSWORD}', MASTER_PORT=3306, MASTER_LOG_FILE='${FILE2}', MASTER_LOG_POS=${POSITION2};
START SLAVE;
"

echo "Unlock tables"
docker exec grafana_onepage_project-mariadb1-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -Nse "UNLOCK TABLES;"
docker exec grafana_onepage_project-mariadb2-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -Nse "UNLOCK TABLES;"

SLAVE_STATUS1=$(docker exec grafana_onepage_project-mariadb1-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -e "SHOW SLAVE STATUS\G")
echo "${SLAVE_STATUS1}"
SLAVE_STATUS2=$(docker exec grafana_onepage_project-mariadb2-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -e "SHOW SLAVE STATUS\G")
echo "${SLAVE_STATUS2}"

SERVICES_UP_STATUS=$(docker-compose -f ${PWD}/compose.yaml up -d)
echo ${SERVICES_UP_STATUS}

echo "Configure logging for databases"
docker exec grafana_onepage_project-mariadb1-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -e "
SET global general_log = 1;
SET global log_output = 'table';
"
docker exec grafana_onepage_project-mariadb2-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -e "
SET global general_log = 1;
SET global log_output = 'table';
"

echo "Grant privileges for testing"
docker exec grafana_onepage_project-mariadb1-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -e "
GRANT ALL PRIVILEGES ON test_${DB_NAME}.* TO '${DB_USER}'@'%';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';
"
docker exec grafana_onepage_project-mariadb2-1 mariadb -u root -p${MARIADB_ROOT_PASSWORD} -e "
GRANT ALL PRIVILEGES ON test_${DB_NAME}.* TO '${DB_USER}'@'%';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';
"

until $(curl --output /dev/null --silent --head --fail http://"$GRAFANA_HOST":3000); do
    echo "Waiting for Grafana to start..."
    sleep 5
done

echo "Grafana started successfully."
echo "Creating user"
curl -X POST http://"$GRAFANA_HOST":3000/api/admin/users \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Basic $(echo -n admin:admin | base64)" \
    -d '{
        "name": "API test user",
        "email": "'"$GRAFANA_USER_EMAIL"'",
        "login": "'"$GRAFANA_USER"'",
        "password": "'"$GRAFANA_USER_PASSWORD"'",
        "OrgId": 1
    }'

echo "Changing admin password"
curl -X PUT http://"$GRAFANA_HOST":3000/api/admin/users/1/password \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Basic $(echo -n admin:admin | base64)" \
    -d '{
        "password": "'"$GRAFANA_ADMIN_PASSWORD"'"
    }'

echo "Star Dashboard 1"
curl -X POST http://"$GRAFANA_HOST":3000/api/user/stars/dashboard/1 \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Basic $(echo -n "$GRAFANA_USER":"$GRAFANA_USER_PASSWORD" | base64)"

echo "Star Dashboard 2"
curl -X POST http://"$GRAFANA_HOST":3000/api/user/stars/dashboard/2 \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Basic $(echo -n "$GRAFANA_USER":"$GRAFANA_USER_PASSWORD" | base64)"

echo "End time: $(date)"