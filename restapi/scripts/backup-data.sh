#!/usr/bin/env bash
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -t -A -F "," -c "copy (select * from users) to STDOUT with CSV HEADER DELIMITER ','" > ./migration_data/users_bak.csv
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -t -A -F "," -c "copy (select * from institutions) to STDOUT with CSV HEADER DELIMITER ','" > ./migration_data/institutions_bak.csv
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -t -A -F "," -c "copy (select * from guardians) to STDOUT with CSV HEADER DELIMITER ','" > ./migration_data/guardians_bak.csv
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -t -A -F "," -c "copy (select * from location_services) to STDOUT with CSV HEADER DELIMITER ','" > ./migration_data/location_services_bak.csv
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -t -A -F "," -c "copy (select * from clients) to STDOUT with CSV HEADER DELIMITER ','" > ./migration_data/clients_bak.csv
docker exec -t restapi_postgres_1 psql -U bhaktirahayu -t -A -F "," -c "copy (select * from covid_checkups) to STDOUT with CSV HEADER DELIMITER ','" > ./migration_data/covid_checkups_bak.csv
