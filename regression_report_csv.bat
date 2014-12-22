REM __author__ = 'alex.galych'
REM __author__ = 'oleg.rudnev'
@ECHO OFF

REM Required:
set NAME="alex.galych"
set SERVER="https://jira.com"
set PROJECT="PROJECT"
set PASSWORD="pass"
set START_DATE="2014-11-19 00:00"
set FIXED_VERSION="Iteration"

REM Optional:
set CALCULATION_DATE=
set CALCULATION_DATE_24_HOUR_START=
set CSV_FILE_NAME=

REM python script attributes.
set PARAMS=--server=%SERVER% --project=%PROJECT% --name=%NAME% --password=%PASSWORD% --iteration_start_date=%START_DATE% --fixed_version=%FIXED_VERSION%

REM add calculation_date to script attributes.
IF defined CALCULATION_DATE (
    set PARAMS=%PARAMS% --calculation_date=%CALCULATION_DATE%
)

REM add csv_file_name to script attributes.
IF defined CSV_FILE_NAME (
    set PARAMS=%PARAMS% --csv_file_name=%CSV_FILE_NAME%
)

REM add calculation_date_start to script attributes.
IF defined CALCULATION_DATE_24_HOUR_START (
    set PARAMS=%PARAMS% --calculation_date_start=%CALCULATION_DATE_24_HOUR_START%
)

ECHO Automation of QA Regression metrics reports start...

c:\python27\python.exe %~dp0\regression_report_csv.py %PARAMS%

ECHO Automation of QA Regression metrics reports end.
PAUSE
