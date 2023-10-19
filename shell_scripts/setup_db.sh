#!/bin/bash

echo "The value of S3_BUCKET is: ${S3_BUCKET}"
echo "The value of S3_FILE is: ${S3_FILE}"
echo "The value of DB_NAME is: ${DB_NAME}"

# update 
sudo apt-get update -y && sudo apt-get upgrade -y

#  download AWS CLI
sudo apt-get install awscli -y

# Download postgres and postgres-contrib
sudo apt-get install postgresql postgresql-contrib -y

# Alter the password for the postgres user
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '${DB_PASSWORD}';"

# make changes to pg_hba.conf file
sudo sed -i '/# Database administrative login by Unix domain socket/!b;n;c\local   all             postgres                                trust' /etc/postgresql/14/main/pg_hba.conf
# sudo sed -i '/# Database administrative login by Unix domain socket/!b;n;c\local   all             postgres                                md5' /etc/postgresql/14/main/pg_hba.conf

sudo sh -c "echo 'host    all             all             0.0.0.0/0               trust' >> /etc/postgresql/14/main/pg_hba.conf"
# sudo sh -c "echo 'host    all             all             0.0.0.0/0               md5' >> /etc/postgresql/14/main/pg_hba.conf"
# sudo sh -c "echo 'host all all 0.0.0.0/0 md5' >> /etc/postgresql/14/main/pg_hba.conf"

sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/14/main/postgresql.conf

# sudo service postgresql restart
sudo systemctl restart postgresql

# Create a custom directory in /usr/local
sudo mkdir /usr/local/s3_downloads

# copy file from S3 bucket
sudo aws s3 cp s3://${S3_BUCKET}/${S3_FILE} /usr/local/s3_downloads/${S3_FILE}
# sudo aws s3 cp s3://dish-recipes-bucket/dish_recipes2.csv /usr/local/s3_downloads/dish_recipes2.csv

# CREATE DATABASE
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER = postgres ENCODING = 'UTF-8';"
# sudo -u postgres psql -c "CREATE DATABASE dish_db3 OWNER = postgres ENCODING = 'UTF-8';"
# sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER = postgres;"

# s3://${S3_BUCKET}/${S3_FILE}

# CREATE TABLE IN DATABASE
sudo -u postgres psql ${DB_NAME} -c "
    CREATE TABLE dish_table (
        dish_id SERIAL PRIMARY KEY,
        dish TEXT,
        ingredients JSONB,
        quantities JSONB,
        directions JSONB
    );"

# # CREATE TABLE IN DATABASE (OLD VERSION)
# sudo -u postgres psql ${DB_NAME} -c "
#     CREATE TABLE dish_table (
#         dish_id SERIAL PRIMARY KEY,
#         uid TEXT,
#         dish TEXT,
#         ingredients JSONB,
#         split_ingredients JSONB,
#         quantities JSONB,
#         directions JSONB
#     );"

sudo -u postgres psql -d ${DB_NAME} -c "\copy dish_table FROM 'usr/local/s3_downloads/${S3_FILE}' DELIMITER ',' CSV HEADER;"
# sudo -u postgres psql -d dish_db -c "\copy dish_table FROM '/usr/local/s3_downloads/dish_recipes2.csv' DELIMITER ',' CSV HEADER;"

# create directions table (directions_table)
sudo -u postgres psql ${DB_NAME} -c "
    CREATE TABLE directions_table (
        dish_id SERIAL PRIMARY KEY,
        dish TEXT,
        directions JSONB,
        FOREIGN KEY (dish_id) REFERENCES dish_table(dish_id)
    );"

# create quantities table (quantities_table)
sudo -u postgres psql ${DB_NAME} -c "
    CREATE TABLE quantities_table (
        dish_id SERIAL PRIMARY KEY,
        dish TEXT,
        quantities JSONB,
        FOREIGN KEY (dish_id) REFERENCES dish_table(dish_id)
    );"

# # create details table (details_table)
# sudo -u postgres psql ${DB_NAME} -c "
#     CREATE TABLE details_table (
#         dish_id SERIAL PRIMARY KEY,
#         dish TEXT,
#         quantities JSONB,
#         directions JSONB,
#         FOREIGN KEY (dish_id) REFERENCES dish_table(dish_id)
#     );"

# # Insert dish_id, dish, quantities, directions into details_table from dish_table
# sudo -u postgres psql ${DB_NAME} -c "INSERT INTO details_table (dish_id, dish, quantities, directions)
#     SELECT dish_id, dish, quantities, directions
#     FROM dish_table;"

# Insert dish_id, dish, DIRECTIONS into directions_table from dish_table
sudo -u postgres psql ${DB_NAME} -c "INSERT INTO directions_table (dish_id, dish, directions)
    SELECT dish_id, dish, directions
    FROM dish_table;"

# Insert dish_id, dish, QUANTITIES into directions_table from dish_table
sudo -u postgres psql ${DB_NAME} -c "INSERT INTO quantities_table (dish_id, dish, quantities)
    SELECT dish_id, dish, quantities
    FROM dish_table;"

# Drop split_ingredients, quantities, directions from main dish_table
sudo -u postgres psql ${DB_NAME} -c "ALTER TABLE dish_table
    DROP COLUMN IF EXISTS quantities,
    DROP COLUMN IF EXISTS directions;"

# remove CSV file downloaded from S3
sudo rm /usr/local/s3_downloads/${S3_FILE}

# sudo service postgresql restart
sudo systemctl restart postgresql

####################################################################
# # Alter the password for the postgres user
# sudo -u postgres psql -c "ALTER USER postgres password '${DB_PASSWORD}';"
# # psql -c "ALTER USER postgres WITH PASSWORD 'YOUR_NEW_PASSWORD';"

# # # Exit from the postgres user
# # exit

# # make changes to pg_hba.conf file
# sudo sed -i '/# Database administrative login by Unix domain socket/!b;n;c\local   all             postgres                                md5' pg_hba.conf

# sudo sh -c "echo 'host   all     all        0.0.0.0/0                                md5' >> /etc/postgresql/14/main/pg_hba.conf"
# # sudo sh -c "echo 'host all all 0.0.0.0/0 md5' >> /etc/postgresql/14/main/pg_hba.conf"

# # sudo service postgresql restart
# sudo systemctl restart postgresql

# # Switch to postgres user
# sudo su postgres

# # Create a database (adjust dbname and owner as needed)
# sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER = postgres;"
# # sudo -u postgres psql -c "CREATE DATABASE dish_db3 OWNER = postgres;"

# # psql -U postgres -c "CREATE DATABASE ${DB_NAME} OWNER = postgres;"
# # sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER = postgres;"

# # Download Lambda postgres extensions
# sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS aws_lambda CASCADE;"
# # psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS aws_lambda CASCADE;"
# # sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS aws_lambda CASCADE;"

# # Download S3 postgres extensions
# sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS aws_s3 CASCADE;"
# # psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS aws_s3 CASCADE;"
# # sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS aws_s3 CASCADE;"

# # Download S3 postgres extensions
# psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS aws_s3 CASCADE;"
# # sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS aws_s3 CASCADE;"

# # create main dish_table with all columns
# psql -U postgres -d ${DB_NAME} -c "
#     CREATE TABLE dish_table (
#         dish_id SERIAL PRIMARY KEY,
#         uid TEXT,
#         dish TEXT,
#         ingredients JSONB,
#         split_ingredients JSONB,
#         quantities JSONB,
#         directions JSONB
#     );"

# # Import CSV from S3 and put it into dish_table 
# psql -U postgres -d ${DB_NAME} "SELECT aws_s3.table_import_from_s3(
#     'dish_table', 
#     'dish_id,uid,dish,ingredients,split_ingredients,quantities,directions', 
#     '(FORMAT CSV, DELIMITER '','', HEADER true)', 
#     '${S3_BUCKET}', 
#     '${S3_FILE}', 
#     '${AWS_REGION}'
#     );"

# # create details table (details_table)
# psql -U postgres -d ${DB_NAME} "CREATE TABLE details_table (
#         dish_id SERIAL PRIMARY KEY,
#         uid TEXT,
#         split_ingredients JSONB,
#         quantities JSONB,
#         directions JSONB,
#         FOREIGN KEY (dish_id) REFERENCES dish_table(dish_id)
#     );"

# # Insert dish_id, uid, split_ingredients, quantities, directions into details_table from dish_table
# psql -U postgres -d ${DB_NAME} "INSERT INTO details_table (dish_id, uid, split_ingredients, quantities, directions)
#     SELECT dish_id, uid, split_ingredients, quantities, directions
#     FROM dish_table;"
    
# # Drop split_ingredients, quantities, directions from main dish_table
# psql -U postgres -d ${DB_NAME} "ALTER TABLE dish_table
#     DROP COLUMN IF EXISTS split_ingredients,
#     DROP COLUMN IF EXISTS quantities,
#     DROP COLUMN IF EXISTS directions;"

# exit

# sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/14/main/postgresql.conf

# # sudo service postgresql restart
# sudo systemctl restart postgresql
