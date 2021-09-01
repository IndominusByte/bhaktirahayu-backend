#!/usr/bin/env bash
docker-compose exec -T postgres psql -U bhaktirahayu -c "COPY users (username,email,password,role,created_at,updated_at) FROM '/home/users.csv' delimiter ',' csv header;"
