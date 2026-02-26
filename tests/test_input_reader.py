# tests/test_input_reader.py

import pytest
from pathlib import Path
import pandas as pd

from src.timetable_scheduler.input_reader import load_courses, load_rooms, load_minors
from src.timetable_scheduler.config import INPUT_DIR, COURSE_FILE, CLASSROOM_FILE, MINOR_FILE

@pytest.mark.skipif(not COURSE_FILE.exists(), reason="course_data.xlsx not found")
def test_load_courses_basic():
    courses = load_courses()
    assert len(courses) > 0
    for c in courses:
        assert c.code
        assert c.name

@pytest.mark.skipif(not CLASSROOM_FILE.exists(), reason="classroom_data.xlsx not found")
def test_load_rooms_basic():
    rooms = load_rooms()
    assert len(rooms) > 0
    for r in rooms:
        assert r.number
        assert r.capacity > 0

@pytest.mark.skipif(not MINOR_FILE.exists(), reason="minor.xlsx not found")
def test_load_minors_basic():
    minors = load_minors()
    assert len(minors) >= 0
