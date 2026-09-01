-- Signal to the pgBackRest wrapper that all numbered database migrations ran.
-- The marker is created inside PGDATA and survives restarts with the volume.
\! touch /var/lib/postgresql/data/.civil-atlas-init-complete
