FROM postgres:15.7 

# The scale factor that is used by default to generate the raw TPC-H data.
# You can change the value of this environment parameter if you want a different
# size

ENV SCALE_FACTOR=10
COPY TPCH.tar.gz /tmp/TPCH.tar.gz
RUN tar -xvf /tmp/TPCH.tar.gz -C /tmp
# Install build-essential package in order to be able to use make and build
# tpchtools
RUN apt-get update && apt-get install -y build-essential
RUN cd /tmp/TPCH/dbgen && make -f makefile.suite
# Change the user/group to postgres since the scripts under initdb.d are run
# with the postgres user.
RUN chown -R postgres /tmp/TPCH
RUN chgrp -R postgres /tmp/TPCH
COPY generate_tpch_data.sh /docker-entrypoint-initdb.d/generate_tpch_data.sh
COPY create_tpch_schema.sql /docker-entrypoint-initdb.d/create_tpch_schema.sql
COPY import_tpch_data.sql /docker-entrypoint-initdb.d/import_tpch_data.sql