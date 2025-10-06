from dataclasses import dataclass

@dataclass
class TimetableEntry:
    """Timetable entry data model"""
    slot_id: str
    day: str
    time_slot: str
    course_code: str
    course_name: str
    room_id: str
    instructor_id: str
    batch_id: str
    session_type: str  # Lecture, Tutorial, Lab, Self-Study
    
    def to_dict(self):
        """Convert to dictionary for CSV export"""
        return {
            'slot_id': self.slot_id,
            'day': self.day,
            'time_slot': self.time_slot,
            'course_code': self.course_code,
            'course_name': self.course_name,
            'room_id': self.room_id,
            'instructor_id': self.instructor_id,
            'batch_id': self.batch_id,
            'session_type': self.session_type
        }
