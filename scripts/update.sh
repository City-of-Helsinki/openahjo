#!/bin/bash

TIMESTAMP_FORMAT="+%Y-%m-%d %H:%M:%S"
ROOT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

LOG_FILE="/tmp/ahjo-import-$(date "+%Y-%m-%d").log"

if [ -f $ROOT_PATH/local_update_config ]; then
	. $ROOT_PATH/local_update_config
fi

echo --------------------------------- >> $LOG_FILE
echo "$(date "$TIMESTAMP_FORMAT") Starting import" >> $LOG_FILE
echo --------------------------------- >> $LOG_FILE

cd $ROOT_PATH

# Import new documents
python manage.py ahjo_import --traceback $IMPORT_ARGS >> $LOG_FILE 2>&1
if [ $? -ne 0 ]; then
    cat $LOG_FILE
    exit 1
fi

# Index them
python manage.py update_index --traceback -a 2 >> $LOG_FILE 2>&1
if [ $? -ne 0 ]; then
    cat $LOG_FILE
    exit 1
fi

if [ ! -z "$VARNISH_BAN_URL" ]; then
    varnishadm ban req.url ~ "$VARNISH_BAN_URL" >> $LOG_FILE 2>&1
    if [ $? -ne 0 ]; then
        cat $LOG_FILE
        exit 1
    fi
fi

echo "Import completed successfully." >> $LOG_FILE
