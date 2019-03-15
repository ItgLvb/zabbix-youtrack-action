# ------------ START Constants ------------
import sys
import logging

YT_PROJECT_NAME = 'PI'  # ID project in Youtrack
YT_ASSIGNEE = 'zabbix'  # Assignee to after create issue
YT_TYPE = 'Error'  # Youtrack Issue type
YT_SERVICE = 'Zabbix'  # Youtrack Issue service
YT_SUBSYSTEM = 'DevOps'  # Youtrack Issue subsystem
YT_TIME = 'About 1 hour'  # Estimated time
# YT_TIME = 'Undefined'  # Estimated time
YT_COMMENT = "Now is {status}. \n{text}\n\n"  # Add this comment in issue
YT_SERVER = ""
YT_TOKEN = ''
ZBX_SERVER = ""
ZBX_USER = "api"
ZBX_PASSWORD = ''
LOG_FILE_NAME = '/var/log/zabbix/PtZabbixAlertYTWorkflow.log'  # Path to Log-file for debug
LOG_LEVEL = logging.DEBUG
# ------------ END Constants ------------
