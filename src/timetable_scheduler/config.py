# src/timetable_scheduler/config.py

from pathlib import Path
from datetime import time

# Project paths
BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

COURSE_FILE = INPUT_DIR / "course_data.xlsx"
CLASSROOM_FILE = INPUT_DIR / "classroom_data.xlsx"
MINOR_FILE = INPUT_DIR / "minor.xlsx"

# Working days (indexes used in schedule)
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Working hours
WORK_START = time(7, 30)
WORK_END = time(20, 0)

# Minor-only windows
MINOR_WINDOWS = [
    (time(7, 30), time(9, 0)),
    (time(18, 30), time(20, 30)),
]

# Regular class window (non-minor)
REGULAR_WINDOW = (time(9, 0), time(18, 30))

# Lunch break
LUNCH_START = time(12, 30)
LUNCH_END = time(14, 0)

# Slot durations in minutes
TUTORIAL_DURATION = 60
LECTURE_DURATION = 90
MINOR_DURATION = 90
LAB_DURATION = 120

# Required gap between consecutive classes (minutes)
GAP_MINUTES = 15

# Time granularity for internal scanning (minutes)
TIME_GRANULARITY = 15

# Student counts per department
STUDENTS_PER_DEPARTMENT = {
    "CSE": 160,  # 80 + 80
    "DSAI": 80,
    "ECE": 80,
}

CSE_SECTIONS = ["A", "B"]

# Special rooms
LECTURE_ONLY_ROOMS = {"C002", "C003", "C004"}  # only lecture/tutorial
LAB_ROOM_TYPE = "Lab"
CLASSROOM_ROOM_TYPE = "Classroom"


def get_batch_ids(department: str, semester: int):
    """
    Batch IDs:
      CSE_SEM3_SECA, CSE_SEM3_SECB
      DSAI_SEM3
      ECE_SEM3
    """
    department = department.upper()
    if department == "CSE":
        return [f"{department}_SEM{semester}_SEC{sec}" for sec in CSE_SECTIONS]
    else:
        return [f"{department}_SEM{semester}"]


def time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def minutes_to_time(m: int) -> time:
    return time(m // 60, m % 60)


def format_time_range(start_min: int, end_min: int) -> str:
    from datetime import time as _time
    s = minutes_to_time(start_min)
    e = minutes_to_time(end_min)
    return f"{s.strftime('%H:%M')}-{e.strftime('%H:%M')}"
