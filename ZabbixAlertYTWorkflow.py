#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# (c) DevOpsHQ, 2016

# Integration YouTrack and Zabbix alerts.

import yaml

from pyzabbix import ZabbixAPI
import sys
from six.moves.urllib.parse import quote
import logging
import time
import settings
from youtrack.connection import Connection
import re



# ------------ START Setup logging ------------
# Use logger to log information
logger = logging.getLogger()
logger.setLevel(settings.LOG_LEVEL)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Log to file
fh = logging.FileHandler(settings.LOG_FILE_NAME)
fh.setLevel(settings.LOG_LEVEL)
fh.setFormatter(formatter)
logger.addHandler(fh)

# Log to stdout
ch = logging.StreamHandler()
ch.setLevel(settings.LOG_LEVEL)
ch.setFormatter(formatter)
logger.addHandler(ch)  # Use logger to log information

# Log from pyzabbix
log = logging.getLogger('pyzabbix')
log.addHandler(ch)
log.addHandler(fh)
log.setLevel(settings.LOG_LEVEL)
# ------------ END Setup logging ------------


# ------------ START ZabbixAPI block ------------
Zbx = ZabbixAPI(settings.ZBX_SERVER)
Zbx.session.verify = False
Zbx.login(settings.ZBX_USER, settings.ZBX_PASSWORD)


# ------------ END ZabbixAPI block ------------

# ------------ START Function declaration ------------
def ExecAndLog(connection, issueId, command="", comment=""):
    logger.debug("Run command in {issueId}: {command}. {comment}".format(issueId=issueId,
                                                                         command=command,
                                                                         comment=comment
                                                                         ))
    connection.executeCommand(issueId=issueId,
                              command=command,
                              comment=comment,
                              )


# ------------ END Function declaration ------------

def updateIssue(connection, issueId, summary, description):
    connection._req('POST', "/issue/{issueId}?summary={summary}&description={description}".format(
        issueId=issueId,
        summary=quote(summary),
        description=quote(description)
    ))

def Main(sendTo, subject, yamlMessage):
    """
    Workflow Zabbix-YouTrack
    :param sendTo: URL to Youtrack (ex. https://youtrack.example.com)
    :param subject: subject from Zabbix Action
    :param yamlMessage: message from Zabbix Action
    :return:
    """

    # ----- Use below example yamlMessage to debug -----
#     yamlMessage = """Name: 'Test Zabbix-YT workflow, ignore it'
# Text: 'Agent ping (server:agent.ping()): DOWN (1) '
# Hostname: 'server.exmpale.ru'
# Status: "OK"
# Severity: "High"
# EventID: "96976"
# TriggerID: "123456789012" """

    messages = yaml.load(yamlMessage)

    # ----- START Issue parameters -----
    # Correspondence between the YouTrackPriority and ZabbixSeverity
    # Critical >= High
    # Normal < High

    ytPriority = 'Normal'
    if messages['Severity'] == 'Disaster' or messages['Severity'] == 'High':
        ytPriority = 'Critical'

    ytName = "{} ZabbixTriggerID::{}".format(messages['Name'], messages['TriggerID'])
    # ----- END Issue parameters -----

    # ----- START Youtrack Issue description -----
    # Search link to other issue
    searchString = "Hostname: '{}'".format(messages['Hostname'])
    linkToHostIssue = "{youtrack}/issues/{projectname}?q={query}".format(
        youtrack=sendTo,
        projectname=settings.YT_PROJECT_NAME,
        query=quote(searchString, safe='')
    )

    issueDescription = """
{ytName}
-----
{yamlMessage}
-----
- [{zabbix}?action=dashboard.view Zabbix Dashboard]
- Show [{linkToHostIssue} all issue for *this host*]
""".format(
        ytName=ytName,
        yamlMessage=yamlMessage,
        zabbix=settings.ZBX_SERVER,
        linkToHostIssue=linkToHostIssue, )

    # ----- END Youtrack Issue description -----

    # Create connect to Youtrack API
    connection = Connection(sendTo, token=settings.YT_TOKEN)

    # ----- START Youtrack get or create issue -----
    # Get issue if exist
    # Search for TriggerID
    createNewIssue = False

    logger.debug("Get issue with text '{}'".format(messages['TriggerID']))
    issue = connection.getIssues(settings.YT_PROJECT_NAME,
                                 "ZabbixTriggerID::{}".format(messages['TriggerID']),
                                 0,
                                 1)


    if len(issue) == 0:
        createNewIssue = True

    else:
        # if issue contains TriggerID in summary, then it's good issue
        # else create new issue, this is bad issue, not from Zabbix
        if "ZabbixTriggerID::{}".format(messages['TriggerID']) in issue[0]['summary']:
            issueId = issue[0]['id']
            issue = connection.getIssue(issueId)
        else:
            createNewIssue = True

    # Create new issue
    if createNewIssue:
        logger.debug("Create new issue because it is not exist")
        issue = connection.createIssue(settings.YT_PROJECT_NAME,
                                       'Unassigned',
                                       ytName,
                                       issueDescription,
                                       priority=ytPriority,
                                       subsystem=settings.YT_SUBSYSTEM,
                                       state="Open",
                                       type=settings.YT_TYPE,
                                       )
        time.sleep(3)

        # Parse ID for new issue
        result = re.search(r'(PI-\d*)', issue[0]['location'])

        issueId = result.group(0)
        issue = connection.getIssue(issueId)

    logger.debug("Issue have id={}".format(issueId))

    # Set issue service
    ExecAndLog(connection, issueId, "Исполнитель {}".format(settings.YT_SERVICE))

    # Update priority
    ExecAndLog(connection, issueId, "Priority {}".format(ytPriority))

    # ----- END Youtrack get or create issue -----

    # ----- START PROBLEM block ------
    if messages['Status'] == "PROBLEM":

        # Reopen if Fixed or Verified or Canceled
        if issue['State'] == u"На тестировании" or issue['State'] == u"Завершена" or issue['State'] == u"Исполнение не планируется":
            # Reopen Issue
            ExecAndLog(connection, issueId, "State Open")

            # Assignee issue
            ExecAndLog(connection, issueId, command="Assignee Unassigned")

        # Update summary and description for issue
        logger.debug("Run command in {issueId}: {command}".format(issueId=issueId,
                                                                  command="""Update summary and description with connection.updateIssue method"""
                                                                  ))
        updateIssue(connection, issueId=issueId, summary=ytName, description=issueDescription)

        # Add comment
        logger.debug("Run command in {issueId}: {command}".format(issueId=issueId,
                                                                  command="""Now is PROBLEM {}""".format(
                                                                      messages['Text'])
                                                                  ))
        connection.executeCommand(issueId=issueId,
                                  command="",
                                  comment=settings.YT_COMMENT.format(
                                      status=messages['Status'],
                                      text=messages['Text'])
                                  )

        # Send ID to Zabbix:
        logger.debug("ZABBIX-API: Send Youtrack ID to {}".format(messages['EventID']))
        Zbx.event.acknowledge(eventids=messages['EventID'], message="Create Youtrack task")
        Zbx.event.acknowledge(eventids=messages['EventID'],
                              message=(settings.YT_SERVER + "/issue/{}").format(issueId))
    # ----- End PROBLEM block ------


    # ----- Start OK block -----
    if messages['Status'] == "OK":

        if issue['State'] == u"На тестировании":
            # Verify if Fixed
            ExecAndLog(connection, issueId, command="State Завершена")
        else:
            if issue['State'] == u"Открыта":
                ExecAndLog(connection, issueId, command="State Исполнение не планируется")

        logger.debug("Run command in {issueId}: {command}".format(issueId=issueId,
                                                                  command="""Now is OK {}""".format(messages['Text'])
                                                                  ))
        connection.executeCommand(issueId=issueId,
                                  command="",
                                  comment=settings.YT_COMMENT.format(
                                      status=messages['Status'],
                                      text=messages['Text'])
                                  )
        # ----- End OK block -----


if __name__ == "__main__":

    logger.debug("Start script with arguments: {}".format(sys.argv[1:]))

    try:
        Main(
            # Arguments WIKI: https://www.zabbix.com/documentation/3.0/ru/manual/config/notifications/media/script
            settings.YT_SERVER,  # to
            sys.argv[2],  # subject
            sys.argv[3],  # body

            # FYI: Next argument used in code:
            # sys.argv[4],  # YT_PASSWORD
            # sys.argv[5],  # ZBX_PASSWORD
        )

    except Exception:
        logger.exception("Exit with error")  # Output exception
        exit(1)

