#!/usr/bin/env bash
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -c "COPY users FROM '/home/users_bak.csv' DELIMITER ',' CSV HEADER"
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -c "COPY users FROM '/home/institutions_bak.csv' DELIMITER ',' CSV HEADER"
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -c "COPY users FROM '/home/guardians_bak.csv' DELIMITER ',' CSV HEADER"
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -c "COPY users FROM '/home/location_services_bak.csv' DELIMITER ',' CSV HEADER"
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -c "COPY users FROM '/home/clients_bak.csv' DELIMITER ',' CSV HEADER"
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -c "COPY users FROM '/home/covid_checkups_bak.csv' DELIMITER ',' CSV HEADER"
