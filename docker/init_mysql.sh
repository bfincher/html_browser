#!/bin/bash

DB_DIR=${APP_CONFIG}/mysql

if [ ! -d $DB_DIR ]; then
    mkdir $DB_DIR
fi

ls -A $DB_DIR > /dev/null || mysql_install_db --user=mysql --datadir=$DB_DIR

rc-service mariadb start

mysqladmin -u root password "${DB_ROOT_PASS}"

echo "GRANT ALL ON *.* TO ${DB_USER}@'127.0.0.1' IDENTIFIED BY '${DB_PASS}' WITH GRANT OPTION;" > /tmp/sql
echo "GRANT ALL ON *.* TO ${DB_USER}@'localhost' IDENTIFIED BY '${DB_PASS}' WITH GRANT OPTION;" >> /tmp/sql
echo "GRANT ALL ON *.* TO ${DB_USER}@'::1' IDENTIFIED BY '${DB_PASS}' WITH GRANT OPTION;" >> /tmp/sql
echo "DELETE FROM mysql.user WHERE User='';" >> /tmp/sql
echo "DROP DATABASE test;" >> /tmp/sql
echo "FLUSH_PRIVILEGES;" >> /tmp/sql
echo "CREATE DATABASE IF NOT EXISTS hb_db; >> /tmp/sql
cat /tmp/sql | msyql -u root --password="${DB_ROOT_PASS}"
rm /tmp/sql