__author__ = 'alex.galych'

import sys
import csv
import datetime
from collections import OrderedDict
from jira.client import JIRA

DATE_FORMAT = "%Y-%m-%d %H:%M"
PARAMS = {
    'server': '', 'name': '', 'password': '', 'project': '', 'iteration_start_date': '', 'fixed_version': '',
    'calculation_date': datetime.datetime.now().strftime(DATE_FORMAT), 'csv_file_name': 'result'
}
RESULT = OrderedDict([
    ('Total opened bugs before testing', 'N/A'),
    ('Total opened bugs', 'N/A'),
    ('Bug that was reported during last 24h ( last day)', 'N/A'),
    ('Backend bugs', 'N/A'),
    ('Frontend bugs', 'N/A'),
    ('Other bugs', 'N/A'),
    ('Priority. Low', 'N/A'),
    ('Priority. Normal', 'N/A'),
    ('Priority. High', 'N/A'),
    ('Priority. Urgent', 'N/A'),
    ('Priority. Now', 'N/A'),
    ('Fixed bugs', 'N/A'),
    ('Fixed bugs since start iteration', 'N/A'),
    ('Resolved during last 24h', 'N/A'),
    ('Unversioned bugs', 'N/A')
])
STATUSES = {
    'Open': "Open",
    'In_Progress': "In Progress",
    'Reopened': "Reopened",
    'Resolved': "Resolved",
    'Closed': "Closed",
    'Feedback': "Feedback required",
    'Rejected': "Rejected",
    'Fixed_locally': "Fixed locally",
    'Fixed_staging': "Fixed on staging",
    'Fixed_production': "Fixed on production",
    'Blocked': "Blocked"
}
BUG_TYPES = {
    'Backend': 'Backend',
    'Frontend': 'Frontend'
}
BUG_PRIORITIES = {
    'Low': 'Low',
    'Normal': 'Normal',
    'High': 'High',
    'Urgent': 'Urgent',
    'Now': 'Now',
}
MAX_RESULT = 300
ISSUE_FIELDS = 'key'
ISSUE_TYPE = 'Bug Report'
EMPTY_FIX_VERSION = 'EMPTY'

# bug statuses combination.
STATUSES_OPEN = ', '.join('"{0}"'.format(w) for w in [STATUSES['Open'], STATUSES['Reopened'], STATUSES['Feedback'],
                                                      STATUSES['In_Progress'], STATUSES['Rejected']])
STATUSES_REJECTED_CLOSED = ', '.join('"{0}"'.format(w)
                                     for w in [STATUSES['Resolved'], STATUSES['Closed'], STATUSES['Rejected']])
STATUSES_FIXED_CLOSED = ', '.join('"{0}"'.format(w) for w in [STATUSES['Resolved'], STATUSES['Closed'],
                                                              STATUSES['Fixed_staging'], STATUSES['Fixed_production']])
STATUSES_CLOSED = ', '.join('"{0}"'.format(w) for w in [STATUSES['Resolved'], STATUSES['Closed']])


# Retrieve params from command line arguments.
def get_command_line_params():
    for arg in sys.argv:
        arg_arr = arg.split('=', 1)
        arg_key = arg_arr[0].replace('--', '')
        if len(arg_arr) == 2 and arg_key in PARAMS:
            PARAMS[arg_key] = arg_arr[1]


# Validate command line arguments.
def validate_command_line_params():
    for parameter in PARAMS:
        if PARAMS[parameter] == '':
            raise Exception('"--' + parameter + '" key should be defined.')


# Establish connection with Jira.
def connect_to_jira():
    try:
        jira_options = {'server': PARAMS['server'], 'verify': False}
        connection = JIRA(options=jira_options, basic_auth=(PARAMS['name'], PARAMS['password']))
    except Exception as e:
        raise Exception("Connection with Jira not established. (" + str(e) + ")")
    return connection


# Get count of jira issues.
def get_jira_found_issues_count(jira, query):
    return len(jira.search_issues(query, maxResults=MAX_RESULT, fields=ISSUE_FIELDS))


# Get calculation_date previous day date (-24hour).
def get_calculation_prev_day_date():
    return (datetime.datetime.strptime(PARAMS['calculation_date'], DATE_FORMAT)
            - datetime.timedelta(days=1)).strftime(DATE_FORMAT)


# Get total opened bugs before testing.
def get_total_open_bugs_before_testing(jira):
    pattern = 'project = "%PROJECT%" AND issuetype = "%ISSUE_TYPE%" ' \
              'AND status NOT IN (%STATUSES%) AND createdDate <= "%DATE%"'
    query = pattern.replace('%PROJECT%', PARAMS['project'])\
                   .replace('%ISSUE_TYPE%', ISSUE_TYPE)\
                   .replace('%STATUSES%', STATUSES_REJECTED_CLOSED)\
                   .replace('%DATE%', PARAMS['iteration_start_date'])
    RESULT['Total opened bugs before testing'] = get_jira_found_issues_count(jira, query)


# Get total opened bugs.
def get_total_opened_bugs(jira):
    pattern = 'project = "%PROJECT%" AND issuetype = "%ISSUE_TYPE%" ' \
              'AND status NOT IN (%STATUSES%) AND fixVersion = "%VERSION%"'
    query = pattern.replace('%PROJECT%', PARAMS['project'])\
                   .replace('%ISSUE_TYPE%', ISSUE_TYPE)\
                   .replace('%STATUSES%', STATUSES_FIXED_CLOSED)\
                   .replace('%VERSION%', PARAMS['fixed_version'])
    RESULT['Total opened bugs'] = get_jira_found_issues_count(jira, query)


# Get bug that was reported during last 24h ( last day).
def get_bugs_reported_during_last_day(jira):
    pattern = 'project = "%PROJECT%" AND issuetype = "%ISSUE_TYPE%" AND fixVersion = "%VERSION%" ' \
              'AND created >= "%CREATED_START%" AND created <= "%CREATED_END%"'
    query = pattern.replace('%PROJECT%', PARAMS['project'])\
                   .replace('%ISSUE_TYPE%', ISSUE_TYPE)\
                   .replace('%VERSION%', PARAMS['fixed_version'])\
                   .replace('%CREATED_START%', get_calculation_prev_day_date())\
                   .replace('%CREATED_END%', PARAMS['calculation_date'])
    RESULT['Bug that was reported during last 24h ( last day)'] = get_jira_found_issues_count(jira, query)


# Get backend, frontend and other bugs.
def get_bugs_by_type(jira, bug_type):
    pattern = 'project = "%PROJECT%" AND issuetype = "%ISSUE_TYPE%" AND status NOT IN (%STATUSES%) ' \
              'AND fixVersion = "%VERSION%" AND "Bug Type" %BUG_TYPE_CONDITION%'

    condition = ('=' + bug_type) if (bug_type in ('Backend', 'Frontend')) else ' NOT IN ("Backend", "Frontend")'
    query = pattern.replace('%PROJECT%', PARAMS['project'])\
                   .replace('%ISSUE_TYPE%', ISSUE_TYPE)\
                   .replace('%STATUSES%', STATUSES_CLOSED)\
                   .replace('%VERSION%', PARAMS['fixed_version'])\
                   .replace('%BUG_TYPE_CONDITION%', condition)
    RESULT[bug_type + ' bugs'] = get_jira_found_issues_count(jira, query)


# Get bugs by priority.
def get_bugs_by_priority(jira, bug_priority):
    pattern = 'project = "%PROJECT%" AND issuetype = "%ISSUE_TYPE%" AND status NOT IN (%STATUSES%) ' \
              'AND fixVersion = "%VERSION%" AND priority = "%BUG_PRIORITY%"'
    query = pattern.replace('%PROJECT%', PARAMS['project'])\
                   .replace('%ISSUE_TYPE%', ISSUE_TYPE)\
                   .replace('%STATUSES%', STATUSES_CLOSED)\
                   .replace('%VERSION%', PARAMS['fixed_version'])\
                   .replace('%BUG_PRIORITY%', bug_priority)
    RESULT['Priority. ' + bug_priority] = get_jira_found_issues_count(jira, query)


# Get fixed bugs by range.
def get_fixed_bugs_by_range(jira, from_date, key):
    pattern = 'project = "%PROJECT%" AND issuetype = "%ISSUE_TYPE%" AND status IN (%STATUSES%) ' \
              'AND fixVersion = "%VERSION%" AND status was in (%OLD_STATUSES%) DURING (%RANGE%)'
    query = pattern.replace('%PROJECT%', PARAMS['project'])\
                   .replace('%ISSUE_TYPE%', ISSUE_TYPE)\
                   .replace('%STATUSES%', STATUSES_FIXED_CLOSED)\
                   .replace('%VERSION%', PARAMS['fixed_version'])\
                   .replace('%OLD_STATUSES%', STATUSES_OPEN)\
                   .replace('%RANGE%', ', '.join('"{0}"'.format(w) for w in [from_date, PARAMS['calculation_date']]))
    RESULT[key] = get_jira_found_issues_count(jira, query)


# Get bugs that were resolved during last 24h.
def get_bugs_resolved_during_last_day(jira):
    pattern = 'project = "%PROJECT%" AND issuetype = "%ISSUE_TYPE%" AND status IN (%STATUSES%) ' \
              'AND resolved >= "%RESOLVED_START%" AND resolved <= "%RESOLVED_END%" AND fixVersion = "%VERSION%"'
    query = pattern.replace('%PROJECT%', PARAMS['project'])\
                   .replace('%ISSUE_TYPE%', ISSUE_TYPE)\
                   .replace('%STATUSES%', STATUSES_CLOSED)\
                   .replace('%VERSION%', PARAMS['fixed_version'])\
                   .replace('%RESOLVED_START%', get_calculation_prev_day_date())\
                   .replace('%RESOLVED_END%', PARAMS['calculation_date'])
    RESULT['Resolved during last 24h'] = get_jira_found_issues_count(jira, query)


# Get bugs without fixed version.
def get_bugs_without_fixed_version(jira):
    pattern = 'project = "%PROJECT%" AND issuetype = "%ISSUE_TYPE%" ' \
              'AND fixVersion is %VERSION% AND status NOT IN (%STATUSES%)'
    query = pattern.replace('%PROJECT%', PARAMS['project'])\
                   .replace('%ISSUE_TYPE%', ISSUE_TYPE)\
                   .replace('%VERSION%', EMPTY_FIX_VERSION)\
                   .replace('%STATUSES%', STATUSES_CLOSED)
    RESULT['Unversioned bugs'] = get_jira_found_issues_count(jira, query)


# Write result to csv file.
def write_to_csv():
    with open(PARAMS['csv_file_name'] + '.csv', 'wb') as f:
        w = csv.DictWriter(f, RESULT.keys())
        w.writeheader()
        w.writerow(RESULT)
        return


def main():
    try:
        get_command_line_params()
        validate_command_line_params()
        jira = connect_to_jira()

        # get data from jira.
        get_total_open_bugs_before_testing(jira)
        get_total_opened_bugs(jira)
        get_bugs_reported_during_last_day(jira)

        get_bugs_by_type(jira, 'Backend')
        get_bugs_by_type(jira, 'Frontend')
        get_bugs_by_type(jira, 'Other')

        for priority in BUG_PRIORITIES:
            get_bugs_by_priority(jira, priority)

        # get fixed (last 24h)
        get_fixed_bugs_by_range(jira, get_calculation_prev_day_date(), 'Fixed bugs')

        # get fixed bugs since start iteration.
        get_fixed_bugs_by_range(jira, PARAMS['iteration_start_date'], 'Fixed bugs since start iteration')

        get_bugs_resolved_during_last_day(jira)
        get_bugs_without_fixed_version(jira)

        # write data to file.
        write_to_csv()

    except Exception as ex:
        print str(ex)
    else:
        return 0

if __name__ == '__main__':
    main()