#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import datetime as _dt
import time
import stat

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    ZoneInfo = None

# =========================
# Names, digits, constants
# =========================

JALALI_MONTHS_EN = [
    "Farvardin", "Ordibehesht", "Khordaad", "Tir", "Mordaad", "Shahrivar",
    "Mehr", "Aabaan", "Aazar", "Dey", "Bahman", "Esfand"
]
JALALI_MONTHS_FA = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]
JALALI_MONTHS_3_EN = ["Far", "Ord", "Kho", "Tir", "Mor", "Sha", "Meh", "Aba", "Aza", "Dey", "Bah", "Esf"]
JALALI_MONTHS_3_FA = ["فرو", "ارد", "خرد", "تیر", "مرد", "شهر", "مهر", "آبا", "آذر", "دی", "بهم", "اسف"]

JALALI_DAYS_EN = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
JALALI_DAYS_3_EN = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
JALALI_DAYS_2_EN = ["Sa", "Su", "Mo", "Tu", "We", "Th", "Fr"]

# Farsi transliteration version (Latin but Persian names)
JALALI_DAYS_FA_LAT = ["Shanbeh", "Yek-Shanbeh", "Do-Shanbeh", "Seh-Shanbeh", "Chahaar-Shanbeh", "Panj-Shanbeh", "Jomeh"]
JALALI_DAYS_3_FA_LAT = ["Sha", "Yek", "Dos", "Ses", "Cha", "Pan", "Jom"]

JALALI_DAYS_FA = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
JALALI_DAYS_3_FA = ["شنب", "یکش", "دوش", "سهش", "چها", "پنج", "جمع"]
JALALI_DAYS_2_FA = ["شن", "یک", "دو", "سه", "چه", "پن", "جم"]

FARSI_DIGITS = {
    '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
    '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹',
    '-': '-', ' ': ' '
}

ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "white": "\033[37m",
    "red": "\033[31m",
    "bg_white": "\033[47m",
    "fg_black": "\033[30m",
}

# Saturday=0 … Friday=6 (Jalali convention)
def greg_weekday_to_jalali_wday(py_weekday):
    # Python: Monday=0..Sunday=6
    # We want Saturday=0 … Friday=6
    return (py_weekday + 2) % 7

# =========================
# Jalali <-> Gregorian
# ("jalaali-js" algorithm)
# =========================
# This algorithm matches the official Iranian calendar across modern years and
# is battle-tested. It avoids 2820-cycle controversies.

def _is_greg_leap(y):
    return (y % 4 == 0) and (y % 100 != 0 or y % 400 == 0)

def g2j(gy, gm, gd):
    gy2 = gy - 1600
    gm2 = gm - 1
    gd2 = gd - 1
    g_day_no = 365 * gy2 + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
    g_md = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    for i in range(gm2):
        g_day_no += g_md[i]
    if gm2 > 1 and _is_greg_leap(gy):
        g_day_no += 1
    g_day_no += gd2
    j_day_no = g_day_no - 79
    j_np = j_day_no // 12053
    j_day_no %= 12053
    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461
    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365
    if j_day_no < 186:
        jm = j_day_no // 31 + 1
        jd = (j_day_no % 31) + 1
    else:
        jm = (j_day_no - 186) // 30 + 7
        jd = (j_day_no - 186) % 30 + 1
    return jy, jm, jd

def j2g(jy, jm, jd):
    jy2 = jy - 979
    jm2 = jm - 1
    jd2 = jd - 1
    j_day_no = 365 * jy2 + (jy2 // 33) * 8 + ((jy2 % 33) + 3) // 4
    for i in range(jm2):
        j_day_no += 31 if i < 6 else 30
    j_day_no += jd2
    g_day_no = j_day_no + 79
    gy = 1600 + 400 * (g_day_no // 146097)
    g_day_no %= 146097
    leap = True
    if g_day_no >= 36525:
        g_day_no -= 1
        gy += 100 * (g_day_no // 36524)
        g_day_no %= 36524
        if g_day_no >= 365:
            g_day_no += 1
        else:
            leap = False
    gy += 4 * (g_day_no // 1461)
    g_day_no %= 1461
    if g_day_no >= 366:
        leap = False
        g_day_no -= 1
        gy += g_day_no // 365
        g_day_no %= 365
    g_md = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 12 and g_day_no >= g_md[gm]:
        g_day_no -= g_md[gm]
        gm += 1
    gd = g_day_no + 1
    return gy, gm + 1, gd

def is_jalali_leap(jy):
    # Esfand has 30 days in leap years.
    # Use a quick check: compare j2g(jy, 12, 30) — if valid, leap.
    try:
        j2g(jy, 12, 30)
        return True
    except Exception:
        return False

def jalali_days_in_month(jy, jm):
    if jm < 1 or jm > 12:
        raise ValueError("month out of range")
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    return 30 if is_jalali_leap(jy) else 29

def jalali_yday(jy, jm, jd):
    if jm <= 6:
        return (jm - 1) * 31 + jd - 1
    return (6 * 31) + (jm - 7) * 30 + jd - 1

def to_farsi_digits(s):
    return ''.join(FARSI_DIGITS.get(ch, ch) for ch in str(s))

# Convert between Jalali date and Python datetime (with tz)
def jalali_to_datetime(jy, jm, jd, hour=0, minute=0, second=0, tz=None):
    gy, gm, gd = j2g(jy, jm, jd)
    if tz is None:
        return _dt.datetime(gy, gm, gd, hour, minute, second)
    return _dt.datetime(gy, gm, gd, hour, minute, second, tzinfo=tz)

def datetime_to_jalali(dt):
    return g2j(dt.year, dt.month, dt.day)

# =========================
# Formatting (jstrftime)
# =========================

def jstrftime(fmt, dt, lang="en", farsi_digits=False):
    """
    Format a given datetime dt as Jalali, using fmt codes similar to libjalali:
      %Y, %m, %d, %H, %M, %S, %a, %A, %b, %B, %j, %u, %w, %z, %Z, %D, %F, %T, %R, %c, %x, %X, %%
      Extras (Farsi):
      %g, %G (weekday names), %v, %V (month names), %E (full Farsi line), %W (yyyy/mm/dd Farsi digits)
    """
    jy, jm, jd = datetime_to_jalali(dt)
    # Weekday in Jalali convention
    jalali_wday = greg_weekday_to_jalali_wday(dt.weekday())

    days_full_en = JALALI_DAYS_EN
    days_abbr_en = JALALI_DAYS_3_EN
    months_full_en = JALALI_MONTHS_EN
    months_abbr_en = JALALI_MONTHS_3_EN

    days_full_fa = JALALI_DAYS_FA
    days_abbr_fa = JALALI_DAYS_3_FA
    months_full_fa = JALALI_MONTHS_FA
    months_abbr_fa = JALALI_MONTHS_3_FA

    if lang == "fa":
        day_full = days_full_fa[jalali_wday]
        day_abbr = days_abbr_fa[jalali_wday]
        mon_full = months_full_fa[jm - 1]
        mon_abbr = months_abbr_fa[jm - 1]
    else:
        day_full = days_full_en[jalali_wday]
        day_abbr = days_abbr_en[jalali_wday]
        mon_full = months_full_en[jm - 1]
        mon_abbr = months_abbr_en[jm - 1]

    mapping = {
        "%Y": f"{jy:04d}",
        "%m": f"{jm:02d}",
        "%d": f"{jd:02d}",
        "%H": f"{dt.hour:02d}",
        "%M": f"{dt.minute:02d}",
        "%S": f"{dt.second:02d}",
        "%a": day_abbr,
        "%A": day_full,
        "%b": mon_abbr,
        "%B": mon_full,
        "%j": f"{jalali_yday(jy, jm, jd)+1:03d}",
        "%u": str(jalali_wday + 1),
        "%w": str(jalali_wday),
        "%D": f"{jy}/{jm:02d}/{jd:02d}",
        "%F": f"{jy}-{jm:02d}-{jd:02d}",
        "%T": f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}",
        "%R": f"{dt.hour:02d}:{dt.minute:02d}",
        "%x": f"{jd:02d}/{jm:02d}/{jy}",
        "%X": f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}",
        "%%": "%",
    }

    # Timezone parts
    tzname = dt.tzname() if dt.tzinfo else time.tzname[0] if time.tzname else "UTC"
    mapping["%Z"] = tzname or ""
    if dt.tzinfo:
        off = dt.utcoffset() or _dt.timedelta(0)
    else:
        # local offset approximation
        off = _dt.datetime.now().astimezone().utcoffset() or _dt.timedelta(0)
    sign = "+" if off >= _dt.timedelta(0) else "-"
    total_m = abs(int(off.total_seconds()) // 60)
    mapping["%z"] = f"{sign}{total_m//60:02d}{total_m%60:02d}"

    # Composite %c (locale-ish)
    mapping["%c"] = f"{day_abbr} {mon_abbr} {jd:02d} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} {tzname} {jy}"

    # Farsi extras:
    mapping["%g"] = days_abbr_fa[jalali_wday]
    mapping["%G"] = days_full_fa[jalali_wday]
    mapping["%v"] = months_abbr_fa[jm - 1]
    mapping["%V"] = months_full_fa[jm - 1]
    mapping["%W"] = f"{to_farsi_digits(jy)}/{to_farsi_digits(f'{jm:02d}')}/{to_farsi_digits(f'{jd:02d}')}"
    # %E: e.g. "سه‌شنبه ۱۷ خرداد ۱۳۹۰، ساعت ۰۸:۱۹:۲۳ - IRDT/UTC"
    mapping["%E"] = f"{days_full_fa[jalali_wday]} {to_farsi_digits(jd)} {months_full_fa[jm-1]} {to_farsi_digits(jy)}، ساعت {to_farsi_digits(f'{dt.hour:02d}')}:{to_farsi_digits(f'{dt.minute:02d}')}:{to_farsi_digits(f'{dt.second:02d}')} - {tzname or 'UTC'}"
    # %O: AM/PM in Persian
    mapping["%O"] = "ق.ظ" if dt.hour < 12 else "ب.ظ"
    # %p / %P
    mapping["%p"] = "AM" if dt.hour < 12 else "PM"
    mapping["%P"] = "am" if dt.hour < 12 else "pm"

    out = fmt
    # Replace longest tokens first to avoid accidental overlaps
    keys = sorted(mapping.keys(), key=len, reverse=True)
    for k in keys:
        out = out.replace(k, mapping[k])

    if farsi_digits:
        out = to_farsi_digits(out)
    return out

# =========================
# Calendar rendering
# =========================

def render_month(jy, jm, highlight=None, show_julian=False, lang="en", farsi_digits=False, color=True, start_wday="sat"):
    # Build a 6x7 grid (rows, cols) for days
    # start_wday: 'sat' (default), 'sun', 'mon'
    if start_wday == "sat":
        base_shift = 0
    elif start_wday == "sun":
        base_shift = 6  # Saturday->6, Sunday->0
    elif start_wday == "mon":
        base_shift = 5  # Saturday->5, Monday->0
    else:
        base_shift = 0

    jdm = jalali_days_in_month(jy, jm)
    # Weekday of first day of month (Jalali)
    g_first = j2g(jy, jm, 1)
    first_py_wday = _dt.date(*g_first).weekday()  # Monday=0..Sunday=6
    first_jwday = greg_weekday_to_jalali_wday(first_py_wday)
    first_col = (first_jwday - base_shift) % 7

    grid = [[None for _ in range(7)] for _ in range(6)]
    r, c = 0, first_col
    for day in range(1, jdm + 1):
        grid[r][c] = day
        c += 1
        if c > 6:
            c = 0
            r += 1

    # Titles
    if lang == "fa":
        mname = JALALI_MONTHS_FA[jm - 1]
        days_hdr = JALALI_DAYS_2_FA if not show_julian else JALALI_DAYS_3_FA
    elif lang == "fa-lat":
        mname = JALALI_MONTHS_EN[jm - 1]  # keep latin month but you can use Persian transliteration
        days_hdr = JALALI_DAYS_3_FA_LAT
    else:
        mname = JALALI_MONTHS_EN[jm - 1]
        days_hdr = JALALI_DAYS_2_EN if not show_julian else JALALI_DAYS_3_EN

    title = f"{mname} {jy}"
    if farsi_digits and lang == "fa":
        title = f"{mname} {to_farsi_digits(jy)}"

    # Print
    out = []
    out.append(title.center(20))
    out.append(' '.join([d.center(2) for d in days_hdr]))
    for row in grid:
        parts = []
        for d in row:
            if d is None:
                parts.append("  ")
            else:
                text = f"{d:2d}"
                if farsi_digits and lang == "fa":
                    text = to_farsi_digits(f"{d:2d}")
                cur = text
                if highlight and d == highlight and color:
                    cur = f"{ANSI['fg_black']}{ANSI['bg_white']}{cur}{ANSI['reset']}"
                parts.append(cur)
        out.append(' '.join(parts))
    return "\n".join(out)

def render_multi_month(jy, jm, count=1, margin=3, **kwargs):
    # Render count months horizontally
    blocks = [render_month(jy, jm + i, **kwargs) if jm + i <= 12 else render_month(jy + (jm + i - 1)//12, (jm + i - 1)%12 + 1, **kwargs) for i in range(count)]
    lines_list = [b.splitlines() for b in blocks]
    heights = [len(lines) for lines in lines_list]
    H = max(heights)
    # Normalize height by padding
    for lines in lines_list:
        while len(lines) < H:
            lines.append("")

    # Join with margin
    space = " " * margin
    out_lines = []
    for i in range(H):
        out_lines.append(space.join(lines[i] for lines in lines_list))
    return "\n".join(out_lines)

# =========================
# CLI: date-like
# =========================

def parse_jalali_date(s):
    # expects "YYYY/MM/DD"
    try:
        y, m, d = s.strip().split("/")
        return int(y), int(m), int(d)
    except Exception:
        raise ValueError("Use YYYY/MM/DD for Jalali dates")

def parse_gregorian_date(s):
    # expects "YYYY/MM/DD"
    try:
        y, m, d = s.strip().split("/")
        return int(y), int(m), int(d)
    except Exception:
        raise ValueError("Use YYYY/MM/DD for Gregorian dates")

def get_file_time(path, use_access=False):
    st = os.stat(path)
    return int(st.st_atime if use_access else st.st_mtime)

def cmd_date(args):
    tz = None
    if args.timezone:
        if not ZoneInfo:
            print("zoneinfo unavailable; use Python 3.9+")
            sys.exit(1)
        tz = ZoneInfo(args.timezone)

    # Base time selection
    t = None
    if args.access is not None:
        t = get_file_time(args.access, use_access=True)
    elif args.reference is not None:
        t = get_file_time(args.reference, use_access=False)
    elif args.date is not None:
        # format;value
        fmt, val = None, None
        if ";" in args.date:
            fmt, val = args.date.split(";", 1)
        else:
            print("Use ';' to separate format and date string (e.g. %Y/%m/%d;%d/%m/%Y)")
            sys.exit(2)
        # Parse a Jalali date/time with minimal support: %Y/%m/%d %H:%M:%S
        # We'll focus on date; time optional
        # Example fmt: "%Y/%m/%d %H:%M:%S"
        # We'll parse using Python datetime after converting Jalali -> Gregorian.
        # Extract numbers based on fmt; keep it simple for common fmt.
        tokens = {"%Y": None, "%m": None, "%d": None, "%H": "0", "%M": "0", "%S": "0"}
        # find positions
        # Simple naive parse: replace tokens with '{}' and then split by non-digit.
        tmpfmt = fmt
        for k in tokens:
            tmpfmt = tmpfmt.replace(k, "{}")
        # Create a mapping by scanning digits from val
        # Quick parse: grab all integers from val in order:
        import re
        nums = re.findall(r"\d+", val)
        if not nums:
            print("Could not parse date string")
            sys.exit(2)
        # align with tokens order
        order = [k for k in ["%Y", "%m", "%d", "%H", "%M", "%S"] if k in fmt]
        if len(nums) < len(order):
            print("Not enough date parts in input")
            sys.exit(2)
        for k, n in zip(order, nums):
            tokens[k] = n
        jy = int(tokens["%Y"])
        jm = int(tokens["%m"])
        jd = int(tokens["%d"])
        hh = int(tokens["%H"])
        mm = int(tokens["%M"])
        ss = int(tokens["%S"])
        dt = jalali_to_datetime(jy, jm, jd, hh, mm, ss, tz if args.utc else None)
        t = int(dt.replace(tzinfo=_dt.timezone.utc).timestamp()) if args.utc else int(dt.timestamp())
    elif args.jalali_conv is not None:
        # -j convert Gregorian to Jalali
        gy, gm, gd = parse_gregorian_date(args.jalali_conv)
        jy, jm, jd = g2j(gy, gm, gd)
        print(f"{jy:04d}/{jm:02d}/{jd:02d}")
        return
    elif args.gregorian_conv is not None:
        # -g convert Jalali to Gregorian
        jy, jm, jd = parse_jalali_date(args.gregorian_conv)
        gy, gm, gd = j2g(jy, jm, jd)
        print(f"{gy:04d}/{gm:02d}/{gd:02d}")
        return
    else:
        t = int(time.time())

    # Select base datetime
    if args.utc:
        dt = _dt.datetime.utcfromtimestamp(t).replace(tzinfo=_dt.timezone.utc if tz is None else tz)
    else:
        dt = _dt.datetime.fromtimestamp(t, tz=tz) if tz else _dt.datetime.fromtimestamp(t)

    # Formatting
    if args.rfc2822:
        # %a, %d %b %Y %H:%M:%S %z (Gregorian names for RFC; keep jalali analog below if needed)
        # But our tool is Jalali-first; we'll format using Jalali day/month names:
        out = jstrftime("%a, %d %b %Y %H:%M:%S %z", dt, lang=args.lang, farsi_digits=args.farsi_digits)
        print(out)
        return

    if args.format:
        # Expect +FORMAT like GNU date
        fmt = args.format
        if fmt.startswith("+"):
            fmt = fmt[1:]
        out = jstrftime(fmt, dt, lang=args.lang, farsi_digits=args.farsi_digits)
        print(out)
        return

    # Default output similar to "Thu Aba 02 00:00:00 1392" style
    out = jstrftime("%a %b %d %H:%M:%S %Z %Y", dt, lang=args.lang, farsi_digits=args.farsi_digits)
    print(out)

# =========================
# CLI: cal-like
# =========================

def cmd_cal(args):
    tz = None
    if args.timezone:
        if not ZoneInfo:
            print("zoneinfo unavailable; use Python 3.9+")
            sys.exit(1)
        tz = ZoneInfo(args.timezone)

    # Determine current Jalali date/time
    now = _dt.datetime.now(tz=tz) if not args.utc else _dt.datetime.now(_dt.timezone.utc)
    jy_now, jm_now, jd_now = datetime_to_jalali(now)

    # Parse target date if provided
    if args.year and args.month and args.day:
        jy, jm, jd = args.year, args.month, args.day
    elif args.year and args.month:
        jy, jm, jd = args.year, args.month, 1
    elif args.year:
        jy, jm, jd = args.year, 1, 1
    else:
        jy, jm, jd = jy_now, jm_now, jd_now

    # Which view?
    lang = args.lang
    farsi_digits = args.farsi_digits
    color = not args.no_color
    show_julian = args.julian
    start_wday = args.start_week

    # highlight current day if same month/year
    highlight = jd_now if (jy == jy_now and jm == jm_now and not args.utc) else None

    if args.year_view:
        # print 12 months in 4x3 groups like cal -y
        for row in [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12)]:
            blocks = []
            for m in row:
                # Show highlight only if this is the current month
                hl = jd_now if (jy == jy_now and m == jm_now and not args.utc) else None
                blocks.append(render_month(jy, m, highlight=hl, show_julian=show_julian,
                                           lang=lang, farsi_digits=farsi_digits, color=color, start_wday=start_wday))
            # zip columns
            pad = " " * args.margin
            lines = [b.splitlines() for b in blocks]
            H = max(len(x) for x in lines)
            for L in lines:
                while len(L) < H:
                    L.append("")
            for i in range(H):
                print(pad.join(L[i] for L in lines))
            print()
        return

    if args.three:
        # previous, current, next
        prev_y, prev_m = (jy - 1, 12) if jm == 1 else (jy, jm - 1)
        next_y, next_m = (jy + 1, 1) if jm == 12 else (jy, jm + 1)
        prev_blk = render_month(prev_y, prev_m, highlight=None, show_julian=show_julian,
                                lang=lang, farsi_digits=farsi_digits, color=color, start_wday=start_wday)
        this_blk = render_month(jy, jm, highlight=highlight, show_julian=show_julian,
                                lang=lang, farsi_digits=farsi_digits, color=color, start_wday=start_wday)
        next_blk = render_month(next_y, next_m, highlight=None, show_julian=show_julian,
                                lang=lang, farsi_digits=farsi_digits, color=color, start_wday=start_wday)
        pad = " " * args.margin
        L1, L2, L3 = prev_blk.splitlines(), this_blk.splitlines(), next_blk.splitlines()
        H = max(len(L1), len(L2), len(L3))
        for L in (L1, L2, L3):
            while len(L) < H:
                L.append("")
        for i in range(H):
            print(pad.join([L1[i], L2[i], L3[i]]))
        return

    # Single month
    print(render_month(jy, jm, highlight=highlight, show_julian=show_julian,
                       lang=lang, farsi_digits=farsi_digits, color=color, start_wday=start_wday))

# =========================
# Main / arg parsing
# =========================

def build_parser():
    p = argparse.ArgumentParser(prog="jtools", add_help=False, description="Jalali calendar/date tools in pure Python")
    sp = p.add_subparsers(dest="cmd", required=True)

    # cal
    pc = sp.add_parser("cal", help="Print Jalali calendar")
    pc.add_argument("year", nargs="?", type=int)
    pc.add_argument("month", nargs="?", type=int)
    pc.add_argument("day", nargs="?", type=int)
    pc.add_argument("-1", "--one", action="store_true", help="Show one month (default)")
    pc.add_argument("-3", "--three", action="store_true", help="Show previous, current, next months")
    pc.add_argument("-y", "--year-view", action="store_true", help="Show whole year")
    pc.add_argument("-j", "--julian", action="store_true", help="Show day-of-year (header style)")
    pc.add_argument("-N", "--no-color", action="store_true", help="Disable color highlighting")
    pc.add_argument("-m", "--margin", type=int, default=3, help="Margin between months (default 3)")
    pc.add_argument("--lang", choices=["en", "fa", "fa-lat"], default="en", help="Language for names")
    pc.add_argument("--farsi-digits", action="store_true", help="Use Farsi digits")
    pc.add_argument("--start-week", choices=["sat", "sun", "mon"], default="sat", help="Week start (default sat)")
    pc.add_argument("-u", "--utc", action="store_true", help="Use UTC instead of local time")
    pc.add_argument("-z", "--timezone", metavar="ZONE", help="Time zone (e.g. Asia/Tehran)")

    # date
    pd = sp.add_parser("date", help="Show or format Jalali date/time")
    pd.add_argument("-u", "--utc", action="store_true", help="Use UTC")
    pd.add_argument("-z", "--timezone", metavar="ZONE", help="Time zone (e.g. Asia/Tehran)")
    pd.add_argument("-R", "--rfc2822", action="store_true", help="RFC 2822-like Jalali output")
    pd.add_argument("-d", "--date", metavar="FMT;STRING", help="Parse date described by FMT and STRING")
    pd.add_argument("-a", "--access", metavar="PATH", help="Show last access time of file (Jalali)")
    pd.add_argument("-r", "--reference", metavar="PATH", help="Show last modification time of file (Jalali)")
    pd.add_argument("-j", "--jalali-conv", metavar="YYYY/MM/DD", help="Convert Gregorian -> Jalali (print)")
    pd.add_argument("-g", "--gregorian-conv", metavar="YYYY/MM/DD", help="Convert Jalali -> Gregorian (print)")
    pd.add_argument("--lang", choices=["en", "fa", "fa-lat"], default="en", help="Language for names")
    pd.add_argument("--farsi-digits", action="store_true", help="Use Farsi digits")
    pd.add_argument("format", nargs="?", help="Optional +FORMAT (like GNU date)")

    # help
    sp.add_parser("help", help="Show help")

    return p

def main():
    p = build_parser()
    if len(sys.argv) == 1:
        p.print_help()
        return
    if sys.argv[1] == "help":
        p.print_help()
        return
    args = p.parse_args()
    if args.cmd == "cal":
        cmd_cal(args)
    elif args.cmd == "date":
        cmd_date(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()