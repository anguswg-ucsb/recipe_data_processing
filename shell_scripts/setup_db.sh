#!/bin/bash

sudo apt-get update -y && sudo apt-get upgrade -y

sudo apt-get install postgresql postgresql-contrib -y

# sudo su postgres

# psql -c "CREATE USER ${DB_USERNAME} WITH SUPERUSER PASSWORD '${DB_PASSWORD}';"
# psql -U postgres -c "CREATE ROLE ubuntu;" 
# psql -U postgres -c "ALTER ROLE ubuntu WITH LOGIN;"
# psql -U postgres -c "ALTER USER ubuntu CREATEDB;"
# psql -U postgres -c "ALTER USER ubuntu WITH PASSWORD '$DB_PASSWORD';"
# psql -U postgres \q

# switch to postgres user
sudo -i -u postgres bash << EOF

# Create a superuser with the provided username and password
psql -c "CREATE USER ${DB_USERNAME} WITH SUPERUSER PASSWORD '${DB_PASSWORD}';"

# Exit from the postgres user and the here document
EOF

# create DB and set new user as owner 
sudo -u postgres createdb ${DB_NAME}
#sudo -u postgres createdb --owner=${DB_USERNAME} ${DB_NAME}

# Connect to DB and run SQL commands to create a table
psql -U ${DB_USERNAME} -d ${DB_NAME} -c \
"CREATE TABLE dish_table (
    dish_id SERIAL PRIMARY KEY,
    uid TEXT,
    dish TEXT,
    ingredients JSONB,
    split_ingredients JSONB,
    quantities JSONB,
    directions JSONB
    )"

sudo sh -c "echo 'host all all 0.0.0.0/0 md5' >> /etc/postgresql/14/main/pg_hba.conf"

sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/14/main/postgresql.conf

sudo service postgresql restart

#################
