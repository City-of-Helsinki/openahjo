#!/bin/sh

TIMESTAMP_FORMAT="+%Y-%m-%d %H:%M:%S"
ROOT_PATH="$(dirname "$0")"/..
LOG_FILE="/tmp/ahjo-import-$(date "+%Y-%m-%d").log"

if [ -f $ROOT_PATH/local_update_config ]; then
	. $ROOT_PATH/local_update_config
fi

echo --------------------------------- >> $LOG_FILE
echo "$(date "$TIMESTAMP_FORMAT") Starting import" >> $LOG_FILE
echo --------------------------------- >> $LOG_FILE

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
    varnishadm ban req.url ~ "^/openahjo/" >> $LOG_FILE 2>&1
    if [ $? -ne 0 ]; then
        cat $LOG_FILE
        exit 1
    fi
fi
