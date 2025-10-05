# jcal-ng

A pure Python implementation of Jalali calendar and date tools, replacing the C library with native Python code.

## Features

- **Pure Python**: No external dependencies, no C libraries needed
- **Calendar functionality**: Print Jalali calendars with colors, Farsi/English names, optional Julian day-of-year view, and multi-month/YTD views
- **Date functionality**: Print/format Jalali time with timezone support, file timestamps, RFC 2822 output, and conversion between Jalali and Gregorian
- **Internationalization**: Support for Farsi, English, and Latin transliteration names
- **Farsi digits**: Option to display numbers using Farsi digits (۰۱۲۳۴۵۶۷۸۹)
- **Timezone support**: Using Python's zoneinfo module (Python 3.9+)
- **Multiple views**: Single month, 3-month view, year view
- **Custom formatting**: Support for custom date formats similar to GNU date

## Installation

Simply download the `jtools.py` file and make it executable:

```bash
chmod +x jtools.py
```

## Usage

### Calendar

```bash
# Current month
./jtools.py cal

# 3-month view
./jtools.py cal -3

# Whole year view
./jtools.py cal 1403 -y

# Farsi names and digits
./jtools.py cal --lang fa --farsi-digits

# Start week on Monday
./jtools.py cal --start-week mon

# No colors
./jtools.py cal -N

# Specify timezone
./jtools.py cal -z "Asia/Tehran"
```

### Date

```bash
# Current date/time
./jtools.py date

# UTC time
./jtools.py date -u

# RFC 2822-like output
./jtools.py date -R

# Custom format
./jtools.py date +'%A, %d %B %Y %T %Z'

# Farsi pretty format
./jtools.py date --lang fa --farsi-digits +'%E'

# File modification time
./jtools.py date -r /path/to/file

# Convert Gregorian to Jalali
./jtools.py date -j 2024/10/05

# Convert Jalali to Gregorian
./jtools.py date -g 1403/07/14

# Specify timezone
./jtools.py date -z "Asia/Tehran"
```

## Options

### Calendar options:
- `--lang {en,fa,fa-lat}`: Language for names (default: en)
- `--farsi-digits`: Use Farsi digits
- `--start-week {sat,sun,mon}`: Week start day (default: sat)
- `-N, --no-color`: Disable color highlighting
- `-j, --julian`: Show day-of-year
- `-3, --three`: Show 3 months (prev, current, next)
- `-y, --year-view`: Show whole year
- `-u, --utc`: Use UTC instead of local time
- `-z ZONE, --timezone ZONE`: Time zone (e.g. Asia/Tehran)

### Date options:
- `--lang {en,fa,fa-lat}`: Language for names (default: en)
- `--farsi-digits`: Use Farsi digits
- `-u, --utc`: Use UTC
- `-z ZONE, --timezone ZONE`: Time zone (e.g. Asia/Tehran)
- `-R, --rfc2822`: RFC 2822-like output
- `-d FMT;STRING`: Parse date described by format and string
- `-a PATH, --access PATH`: Show last access time of file
- `-r PATH, --reference PATH`: Show last modification time of file
- `-j YYYY/MM/DD, --jalali-conv YYYY/MM/DD`: Convert Gregorian to Jalali
- `-g YYYY/MM/DD, --gregorian-conv YYYY/MM/DD`: Convert Jalali to Gregorian

## License

MIT License - see the LICENSE file for details.