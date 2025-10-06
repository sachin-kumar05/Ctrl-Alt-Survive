from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Exam:
    """Exam data model"""
    exam_code: str
    course_code: str
    course_name: str
    date: str
    time_slot: str
    room_ids: List[str] = field(default_factory=list)
    student_count: int = 0
    invigilator_ids: List[str] = field(default_factory=list)
    
    def to_dict(self):
        """Convert to dictionary for CSV export"""
        return {
            'exam_code': self.exam_code,
            'course_code': self.course_code,
            'course_name': self.course_name,
            'date': self.date,
            'time_slot': self.time_slot,
            'rooms': ','.join(self.room_ids),
            'student_count': self.student_count,
            'invigilators': ','.join(self.invigilator_ids)
        }


@dataclass
class SeatingPlan:
    """Seating plan data model"""
    exam_code: str
    room_id: str
    seat_allocations: Dict[int, str] = field(default_factory=dict)
    
    def to_list(self):
        """Convert to list of dictionaries for CSV export"""
        return [
            {
                'exam_code': self.exam_code,
                'room_id': self.room_id,
                'seat_number': seat_num,
                'student_id': student_id
            }
            for seat_num, student_id in self.seat_allocations.items()
        ]