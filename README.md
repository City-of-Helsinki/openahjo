OpenAHJO API
============

Installation
------------
Required Debian packages:

    language-pack-fi postgis postgresql-9.1-postgis libxml2-dev libxslt1-dev

Shell commands:

    sudo su postgres
    createuser -R -S -D -P openahjo
    createdb -O openahjo -T template0 -l fi_FI.UTF8 -E utf8 openahjo
    psql openahjo

PostgreSQL commands:

    CREATE EXTENSION postgis;
    CREATE EXTENSION postgis_topology;
