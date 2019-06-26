#!/bin/bash

DB_DIR=${APP_CONFIG}/mysql

if [ ! -d $DB_DIR ]; then
    mkdir $DB_DIR
fi

if [ ! -d /var/run/mysqld ]; then
    mkdir /var/run/mysqld
fi

chown -R mysql:mysql /var/run/mysqld
chown -R mysql:mysql $DB_DIR

[ "$(ls -A $DB_DIR)" ] || mysql_install_db --user=mysql --datadir=$DB_DIR

mysqld --user=mysql --datadir=${DB_DIR} &

while ! mysqladmin ping -h localhost -u root --password=${DB_ROOT_PASS} --silent; do
    sleep 1
done

mysqladmin -u root password "${DB_ROOT_PASS}"

echo "GRANT ALL ON *.* TO ${DB_USER}@'127.0.0.1' IDENTIFIED BY '${DB_PASS}' WITH GRANT OPTION;" > /tmp/sql
echo "GRANT ALL ON *.* TO ${DB_USER}@'localhost' IDENTIFIED BY '${DB_PASS}' WITH GRANT OPTION;" >> /tmp/sql
echo "GRANT ALL ON *.* TO ${DB_USER}@'::1' IDENTIFIED BY '${DB_PASS}' WITH GRANT OPTION;" >> /tmp/sql
echo "DELETE FROM mysql.user WHERE User='';" >> /tmp/sql
echo "DROP DATABASE IF EXISTS test;" >> /tmp/sql
echo "FLUSH PRIVILEGES;" >> /tmp/sql
echo "CREATE DATABASE IF NOT EXISTS ${DB_NAME};" >> /tmp/sql
echo "ALTER DATABASE ${DB_NAME} CHARACTER SET utf8;" >> /tmp/sql
cat /tmp/sql | mysql -u root --password="${DB_ROOT_PASS}"
rm /tmp/sql
