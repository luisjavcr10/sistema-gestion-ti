#!/bin/bash

# Load environment variables
source ../.env

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="../backups"
FILENAME="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"

mkdir -p $BACKUP_DIR

echo "Creating backup of database ${POSTGRES_DB}..."

docker-compose exec -T postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > $FILENAME

if [ $? -eq 0 ]; then
  echo "Backup created successfully: $FILENAME"
else
  echo "Error creating backup"
  rm $FILENAME
  exit 1
fi
