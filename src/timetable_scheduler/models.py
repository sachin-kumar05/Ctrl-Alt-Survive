# src/timetable_scheduler/models.py

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Course:
    code: str
    name: str
    department: str
    semester: int
    l: int
    t: int
    p: int
    s: int
    c: int
    credits: int
    instructors: List[str]
    registered_students: int
    is_elective: bool
    is_half_semester: bool
    half_category: Optional[str] = None


@dataclass
class Room:
    number: str
    type: str  # "Classroom" or "Lab"
    capacity: int
    facilities: str = ""

    @property
    def is_lab(self) -> bool:
        return self.type.strip().lower() == "lab"


@dataclass
class MinorProgram:
    name: str
    registered_students: int


@dataclass
class ScheduledClass:
    day_index: int
    start_minute: int
    duration: int
    batch_id: str
    term: str  # "PRE" or "POST"

    # normal class fields
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    instructor: Optional[str] = None
    room_number: Optional[str] = None

    # minor
    is_minor: bool = False
    minor_name: Optional[str] = None

    # type flags
    is_lab: bool = False
    is_tutorial: bool = False
    is_lecture: bool = False

    # these are not stored as separate records; Excel writer will mark based on time
    is_break: bool = False
    is_lunch: bool = False


@dataclass
class ScheduleResult:
    scheduled_classes: List[ScheduledClass] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    unscheduled: List[str] = field(default_factory=list)
