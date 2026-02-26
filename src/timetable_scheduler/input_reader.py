# src/timetable_scheduler/input_reader.py

import pandas as pd
from typing import List
from .config import COURSE_FILE, CLASSROOM_FILE, MINOR_FILE
from .models import Course, Room, MinorProgram


def _parse_ltpsc(ltsc_str: str):
    parts = str(ltsc_str).split("-")
    if len(parts) != 5:
        raise ValueError(f"Invalid LTPSC format: {ltsc_str}")
    return tuple(int(p) for p in parts)  # L, T, P, S, C


def load_courses() -> List[Course]:
    df = pd.read_excel(COURSE_FILE)

    required_cols = [
        "Course Code",
        "Course Name",
        "Semester",
        "Department",
        "LTPSC",
        "Credits",
        "Instructor",
        "Registered Students",
        "Elective (Yes/No)",
        "Half Semester (Yes/No)",
    ]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing column in course_data.xlsx: {col}")

    courses: List[Course] = []
    for _, row in df.iterrows():
        l, t, p, s, c_val = _parse_ltpsc(row["LTPSC"])
        instructors = [
            inst.strip()
            for inst in str(row["Instructor"]).split(",")
            if str(inst).strip()
        ]
        course = Course(
            code=str(row["Course Code"]).strip(),
            name=str(row["Course Name"]).strip(),
            department=str(row["Department"]).strip().upper(),
            semester=int(row["Semester"]),
            l=l,
            t=t,
            p=p,
            s=s,
            c=c_val,
            credits=int(row["Credits"]),
            instructors=instructors,
            registered_students=int(row["Registered Students"]),
            is_elective=str(row["Elective (Yes/No)"]).strip().lower() == "yes",
            is_half_semester=str(row["Half Semester (Yes/No)"]).strip().lower()
            == "yes",
        )
        courses.append(course)
    return courses


def load_rooms() -> List[Room]:
    df = pd.read_excel(CLASSROOM_FILE)

    required_cols = ["Room Number", "Type", "Capacity"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing column in classroom_data.xlsx: {col}")

    rooms: List[Room] = []
    for _, row in df.iterrows():
        rooms.append(
            Room(
                number=str(row["Room Number"]).strip(),
                type=str(row["Type"]).strip(),
                capacity=int(row["Capacity"]),
                facilities=str(row.get("Facilities", "")),
            )
        )
    return rooms


def load_minors() -> List[MinorProgram]:
    df = pd.read_excel(MINOR_FILE)

    required_cols = ["Minor Program", "Registered Students"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing column in minor.xlsx: {col}")

    minors: List[MinorProgram] = []
    for _, row in df.iterrows():
        minors.append(
            MinorProgram(
                name=str(row["Minor Program"]).strip(),
                registered_students=int(row["Registered Students"]),
            )
        )
    return minors
