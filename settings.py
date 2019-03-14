# ------------ START Constants ------------
import sys
import logging

YT_PROJECT_NAME = 'CM'  # ID project in Youtrack
YT_ASSIGNEE = 'Zabbix'  # Assignee to after create issue
YT_TYPE = 'Error'  # Youtrack Issue type
YT_SERVICE = 'Zabbix'  # Youtrack Issue service
YT_SUBSYSTEM = 'DevOps'  # Youtrack Issue subsystem
YT_USER = 'Zabbix'  # Youtrack Issue create user
YT_PASSWORD = sys.argv[4]  # Youtrack user password
YT_TIME = 'About 1 hour'  # Estimated time
# YT_TIME = 'Undefined'  # Estimated time
YT_COMMENT = "Now is {status}. \n{text}\n\n"  # Add this comment in issue
LOG_FILE_NAME = '/var/log/zabbix/PtZabbixAlertYTWorkflow.log'  # Path to Log-file for debug
# LOG_FILE_NAME = 'PtZabbixAlertYTWorkflow.log'  # Uncomment for debug in Windows-OS

ZABBIX_SERVER = "https://zabbix.example.com/zabbix"
ZBX_USER = "zabbix_api"
ZBX_PASSWORD = sys.argv[5]
LOG_LEVEL = logging.DEBUG
# ------------ END Constants ------------
