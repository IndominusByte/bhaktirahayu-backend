#!/usr/bin/env bash
docker-compose exec -T backend /bin/bash -c 'mkdir alembic/versions'
docker-compose exec -T backend /bin/bash -c 'alembic revision --autogenerate -m "init db"; alembic upgrade head'
docker-compose exec -T backend /bin/bash -c 'rm -rf alembic/versions'

docker-compose exec -T postgres psql -U bhaktirahayu -c "COPY users (username,email,password,role,created_at,updated_at) FROM '/home/users.csv' delimiter ',' csv header;"
