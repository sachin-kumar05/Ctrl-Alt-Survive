# tests/test_room_allocator.py

from src.timetable_scheduler.models import Room
from src.timetable_scheduler.room_allocator import filter_rooms_for_session

def test_filter_rooms_for_session():
    rooms = [
        Room(number="C002", type="Classroom", capacity=80),
        Room(number="L001", type="Lab", capacity=30),
    ]
    suitable = filter_rooms_for_session(
        rooms=rooms,
        is_lab=False,
        is_minor=False,
        required_capacity=60,
    )
    assert any(r.number == "C002" for r in suitable)
    assert all(not r.is_lab for r in suitable)
