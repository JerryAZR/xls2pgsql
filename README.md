# XLS to PostgreSQL GUI Tool

[![OSCS Status](https://www.oscs1024.com/platform/badge/JerryAZR/xls2pgsql.svg?size=small)](https://www.oscs1024.com/project/JerryAZR/xls2pgsql?ref=badge_small)
[![Windows Build](https://github.com/JerryAZR/xls2pgsql/actions/workflows/windows-build.yml/badge.svg)](https://github.com/JerryAZR/xls2pgsql/actions/workflows/windows-build.yml)

A personal project that imports data entries in xls/xlsx/csv sheets to a PostgreSQL database.

## Dependencies

* psycopg2
* xlrd
* openpyxl
* pandas
* pypinyin
* pyqt5

# Build and Run

To build the executable, run `python -m PyInstaller main.spec` or `.\build.bat`.

To run the app directly with python, run `python .\src\main.py`

