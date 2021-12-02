#!/bin/bash
IFS=$'\n'
DATA_PATH="/home/data/NDClab/datasets"
ZOOM_PATH="sourcedata/raw/zoom"

echo "Checking repos in datasets"
for DIR in `ls $DATA_PATH`
do
    if [ -e "$DATA_PATH/$DIR/$ZOOM_PATH" ]; then
        echo "Validating $DIR encryption"
        if [ "cd "$DATA_PATH/$DIR/$ZOOM_PATH"" grep -q 'Permission denied' ]; then
            echo "$DIR is not accessible via your permissions" 
            continue
        fi
        cd "$DATA_PATH/$DIR/$ZOOM_PATH"
        for SUB in *; do
            echo "checking if contents of $SUB are encrypted"
            cd "$DATA_PATH/$DIR/$ZOOM_PATH/$SUB"
            for FILE in *; do
                if "gpg --list-only $FILE" grep -q 'gpg: encrypted with \. passphrase'; then
                    echo "$FILE encrypted"
                else
                    echo "$DATA_PATH/$DIR/$ZOOM_PATH/$SUB/$FILE failed check, notifying tech"
                    # | mail -s "Encrypt validation failed" fsaidmur@fiu.edu
                fi
            done
        done
    fi
done
