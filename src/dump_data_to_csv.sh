#! /bin/bash

SRC_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CSV_DIR=$SRC_DIR/../dat

mkdir -p $CSV_DIR

# Gets the database URL for dumping out csv.
cd $SRC_DIR/../../webapp
export PP_DB_URL=`heroku config:get DATABASE_URL -a project-pavement`

#dumps data into two csvs
psql --dbname=$PP_DB_URL -c "COPY rides TO stdout DELIMITER ',' CSV HEADER;" > $CSV_DIR/rides.csv
psql --dbname=$PP_DB_URL -c "COPY readings TO stdout DELIMITER ',' CSV HEADER;" > $CSV_DIR/readings.csv
