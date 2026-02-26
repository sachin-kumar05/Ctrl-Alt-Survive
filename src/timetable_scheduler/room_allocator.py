# src/timetable_scheduler/room_allocator.py

from typing import List
from .models import Room
from .config import LECTURE_ONLY_ROOMS


def filter_rooms_for_session(
    rooms: List[Room],
    is_lab: bool,
    is_minor: bool,
    required_capacity: int,
) -> List[Room]:
    """
    Enforce:
      - Lab sessions -> only lab rooms
      - Non-lab -> only classroom rooms
      - C002, C003, C004 -> only normal lectures/tutorials (no lab, no minors)
      - Capacity >= required capacity
    """
    suitable: List[Room] = []
    for r in rooms:
        if is_lab:
            if not r.is_lab:
                continue
        else:
            if r.is_lab:
                continue

        # Special: C002, C003, C004 only for normal lecture/tutorial
        if r.number in LECTURE_ONLY_ROOMS and (is_lab or is_minor):
            continue

        # For minors: don't use these special lecture rooms
        if is_minor and r.number in LECTURE_ONLY_ROOMS:
            continue

        if r.capacity < required_capacity:
            continue

        suitable.append(r)
    return suitable
