FROM mysql:8.2.0

# Set environment variables
ENV MYSQL_ROOT_PASSWORD=123
ENV MYSQL_DATABASE=prototype
ENV MYSQL_USER=prototype
ENV MYSQL_PASSWORD=123

# Copy custom configuration
COPY conf.d/my.cnf /etc/mysql/conf.d/

# Copy initialization scripts (order matters - they execute alphabetically)
COPY db/*.sql /docker-entrypoint-initdb.d/

# Copy and setup superuser generator script
COPY generate_superuser.sh /docker-entrypoint-initdb.d/00_generate_superuser.sh
RUN chmod +x /docker-entrypoint-initdb.d/00_generate_superuser.sh

# Expose MySQL port
EXPOSE 3306

# Use the default MySQL entrypoint
CMD ["mysqld"]
