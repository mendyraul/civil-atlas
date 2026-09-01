FROM postgis/postgis:16-3.5

RUN apt-get update \
    && apt-get install -y --no-install-recommends pgbackrest \
    && rm -rf /var/lib/apt/lists/*

COPY ops/pgbackrest/docker-entrypoint.sh /usr/local/bin/civil-atlas-pgbackrest-entrypoint.sh
COPY ops/pgbackrest/archive-command.sh /usr/local/bin/civil-atlas-pgbackrest-archive
RUN chmod 0755 /usr/local/bin/civil-atlas-pgbackrest-entrypoint.sh \
    /usr/local/bin/civil-atlas-pgbackrest-archive

ENTRYPOINT ["/usr/local/bin/civil-atlas-pgbackrest-entrypoint.sh"]
