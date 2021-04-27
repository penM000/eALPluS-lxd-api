#!/bin/bash
sudo mkdir -p /var/log/code-server
sudo touch /var/log/code-server/action.log
sudo chown -R syslog:syslog /var/log/code-server
cat <<EOF | sudo tee /etc/rsyslog.d/00-receive-code-server.conf 
module(load="imtcp")
input(type="imtcp" port="514")
:programname, isequal, "code-server"    -/var/log/code-server/action.log
EOF
sudo systemctl restart rsyslog.service

cat <<EOF | sudo tee /etc/logrotate.d/code-server 
/var/log/code-server/action.log{
    daily
    notifempty
    copytruncate
    dateext
    dateformat .%Y-%m-%d
    compress
    rotate 999999999
}
EOF
sudo systemctl restart logrotate