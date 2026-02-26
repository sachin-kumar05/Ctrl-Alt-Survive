# src/timetable_scheduler/validator.py

from typing import List
from .models import Course, Room, MinorProgram
from .config import STUDENTS_PER_DEPARTMENT


def validate_courses(courses: List[Course]) -> List[str]:
    warnings: List[str] = []
    for c in courses:
        if c.department not in STUDENTS_PER_DEPARTMENT:
            warnings.append(
                f"Warning: Course {c.code} has unknown department {c.department}."
            )
        if c.l < 0 or c.t < 0 or c.p < 0:
            warnings.append(f"Warning: Course {c.code} has negative LTPSC values.")
        if not c.instructors:
            warnings.append(f"Warning: Course {c.code} has no instructor.")
        if c.registered_students <= 0:
            warnings.append(
                f"Warning: Course {c.code} has non-positive registered students "
                f"({c.registered_students})."
            )
    return warnings


def validate_rooms(rooms: List[Room]) -> List[str]:
    warnings: List[str] = []
    seen = set()
    for r in rooms:
        if r.number in seen:
            warnings.append(f"Warning: Duplicate room number {r.number}.")
        seen.add(r.number)
        if r.capacity <= 0:
            warnings.append(f"Warning: Room {r.number} has non-positive capacity.")
        if r.type.strip().lower() not in {"classroom", "lab"}:
            warnings.append(f"Warning: Room {r.number} has unknown type {r.type}.")
    return warnings


def validate_minors(minors: List[MinorProgram]) -> List[str]:
    warnings: List[str] = []
    for m in minors:
        if m.registered_students <= 0:
            warnings.append(
                f"Warning: Minor {m.name} has non-positive registered students "
                f"({m.registered_students})."
            )
    return warnings


def validate_room_capacity_for_courses(
    courses: List[Course], rooms: List[Room]
) -> List[str]:
    warnings: List[str] = []
    if not rooms:
        warnings.append("Warning: No rooms loaded; scheduling impossible.")
        return warnings
    max_cap = max(r.capacity for r in rooms)
    for c in courses:
        if c.registered_students > max_cap:
            warnings.append(
                f"Warning: Course {c.code} has {c.registered_students} students but "
                f"max room capacity is {max_cap}."
            )
    return warnings


def interactive_warning_prompt(all_warnings: List[str]) -> bool:
    if not all_warnings:
        return True
    print("\n=== WARNINGS DETECTED ===")
    for w in all_warnings:
        print(w)
    print("=========================")
    ans = input("Proceed with scheduling despite these warnings? (y/N): ").strip().lower()
    return ans == "y"
