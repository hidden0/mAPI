#!/bin/bash
sudo yum remove grafana postgres* -y
sudo apt-get purge grafana* postgres* -y
rm -f ./conf/dashboard_*
rm -f ./api.key
rm -f ./grafana*
sudo crontab -r
psql -U postgres -c "select pg_terminate_backend(pid) from pg_stat_activity where datname='mnodes';"
psql -U postgres -c "DROP DATABASE mnodes;"
rm -f ./grafana*.deb*
