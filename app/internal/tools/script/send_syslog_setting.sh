#!/bin/bash
cat <<EOF | sudo tee /etc/rsyslog.d/00-send-code-server.conf 
\$ActionQueueType LinkedList
\$ActionQueueMaxDiskSpace 1g
\$ActionQueueFileName codeservertemp
\$ActionResumeRetryCount -1
\$ActionQueueSaveOnShutdown on
:programname, isequal, "code-server"    @@syslog-server:514
EOF
sudo systemctl restart rsyslog.service
