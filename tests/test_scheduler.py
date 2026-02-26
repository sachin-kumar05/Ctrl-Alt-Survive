# tests/test_scheduler.py

from src.timetable_scheduler.models import Course, Room, MinorProgram
from src.timetable_scheduler.scheduler import schedule_all
from src.timetable_scheduler.config import STUDENTS_PER_DEPARTMENT

def minimal_course():
    return Course(
        code="C101",
        name="Test Course",
        department="CSE",
        semester=3,
        l=2, t=1, p=0, s=0, c=3,
        credits=3,
        instructors=["Prof A"],
        registered_students=60,
        is_elective=False,
        is_half_semester=False,
    )

def minimal_room():
    return Room(
        number="C010",
        type="Classroom",
        capacity=80,
        facilities="",
    )

def test_basic_schedule():
    courses = [minimal_course()]
    rooms = [minimal_room()]
    minors = []
    pre, post = schedule_all(courses, rooms, minors)
    assert len(pre.scheduled_classes) > 0  # at least some sessions scheduled
