#!/bin/bash
cd "/tmp/TPC-H V3.0.1/dbgen"
./dbgen -v -s $SCALE_FACTOR
# Remove the final '|' delimiter from every line otherwise data cannot be
# imported in Postgres
sed -i 's/|$//' *.tbl
mkdir /tmp/tpchdata
mv *.tbl /tmp/tpchdata/
