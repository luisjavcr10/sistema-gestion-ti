#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: ./restore_db.sh <backup_file>"
  exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: File $BACKUP_FILE not found"
  exit 1
fi

# Load environment variables
source ../.env

echo "Restoring database ${POSTGRES_DB} from $BACKUP_FILE..."

cat $BACKUP_FILE | docker-compose exec -T postgres psql -U ${POSTGRES_USER} ${POSTGRES_DB}

if [ $? -eq 0 ]; then
  echo "Restore completed successfully"
else
  echo "Error restoring database"
  exit 1
fi
