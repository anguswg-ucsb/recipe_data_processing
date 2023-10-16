FROM postgres:latest

# Path: /docker-entrypoint-initdb.d/
COPY ./init.sql /docker-entrypoint-initdb.d/

# Expose PostgreSQL port
EXPOSE 5432

# Start PostgreSQL
CMD ["postgres"]