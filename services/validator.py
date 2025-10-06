from typing import List, Dict
from models.course import Course
from models.professor import Professor
from models.room import Room
from utils.logger import Logger

class Validator:
    """Service for validating scheduling constraints"""
    
    def __init__(self):
        self.logger = Logger("Validator")
    
    def validate_course(self, course: Course, professors: Dict[str, Professor]) -> bool:
        """Validate course details"""
        if course.instructor_id not in professors:
            self.logger.error(f"Invalid instructor {course.instructor_id} for course {course.course_code}")
            return False
        
        if course.L < 0 or course.T < 0 or course.P < 0:
            self.logger.error(f"Invalid LTP values for course {course.course_code}")
            return False
        
        return True
    
    def check_professor_break(self, prof: Professor, day: str, 
                             current_slot_index: int, last_slot_index: int) -> bool:
        """Check if professor has minimum 3-hour break"""
        if last_slot_index == -1:
            return True
        
        hours_between = current_slot_index - last_slot_index
        return hours_between >= 3
    
    def check_room_capacity(self, room: Room, required_capacity: int) -> bool:
        """Check if room has sufficient capacity"""
        return room.capacity >= required_capacity