#!/usr/bin/env bash
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -c "COPY users FROM '/home/users_bak.csv' DELIMITER ',' CSV HEADER"
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -c "COPY institutions FROM '/home/institutions_bak.csv' DELIMITER ',' CSV HEADER"
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -c "COPY guardians FROM '/home/guardians_bak.csv' DELIMITER ',' CSV HEADER"
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -c "COPY location_services FROM '/home/location_services_bak.csv' DELIMITER ',' CSV HEADER"
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -c "COPY clients (id,nik,name,phone,birth_place,birth_date,gender,address,created_at,updated_at) FROM '/home/clients_bak.csv' DELIMITER ',' CSV HEADER"
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -c "COPY covid_checkups FROM '/home/covid_checkups_bak.csv' DELIMITER ',' CSV HEADER"
