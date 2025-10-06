from typing import List, Dict
from models.course import Course
from models.professor import Professor
from models.room import Room
from models.timetable import TimetableEntry
from services.validator import Validator
from config import Config
from utils.logger import Logger
import random

class TimetableGenerator:
    """Service for generating academic timetables"""
    
    def __init__(self, courses: List[Course], professors: Dict[str, Professor], 
                 rooms: List[Room]):
        self.courses = courses
        self.professors = professors
        self.rooms = rooms
        self.validator = Validator()
        self.logger = Logger("TimetableGenerator")
        self.timetable: List[TimetableEntry] = []
        
        # Track usage
        self.batch_schedule: Dict[str, Dict] = {}
        self.course_daily_count: Dict[str, Dict] = {}
    
    def generate(self) -> List[TimetableEntry]:
        """Generate complete timetable"""
        self.logger.info("Starting timetable generation...")
        
        for course in self.courses:
            if not self.validator.validate_course(course, self.professors):
                continue
            
            self._schedule_course(course)
        
        self.logger.info(f"Generated {len(self.timetable)} timetable entries")
        return self.timetable
    
    def _schedule_course(self, course: Course):
        """Schedule all sessions for a course"""
        sessions_needed = course.total_sessions()
        sessions_scheduled = 0
        
        for day in Config.WORKING_DAYS:
            if sessions_scheduled >= sessions_needed:
                break
            
            # Check if course already scheduled today (R5)
            day_key = f"{course.course_code}-{day}"
            if day_key in self.course_daily_count:
                continue
            
            for slot_idx, time_slot in enumerate(Config.TIME_SLOTS):
                if sessions_scheduled >= sessions_needed:
                    break
                
                # Skip lunch slot (R8)
                if time_slot == Config.LUNCH_SLOT:
                    continue
                
                # Check if batch is free
                if not self._is_batch_free(course.batch_id, day, time_slot):
                    continue
                
                # Check if professor is free
                if not self._is_professor_free(course.instructor_id, day, time_slot):
                    continue
                
                # Find available room
                room_type = 'Lab' if course.needs_lab() and sessions_scheduled >= course.L else 'Lecture'
                room = self._find_available_room(day, time_slot, room_type)
                
                if room:
                    # Create timetable entry
                    session_type = 'Lecture' if sessions_scheduled < course.L else 'Tutorial'
                    entry = TimetableEntry(
                        slot_id=f"{course.course_code}-{sessions_scheduled}",
                        day=day,
                        time_slot=time_slot,
                        course_code=course.course_code,
                        course_name=course.course_name,
                        room_id=room.room_id,
                        instructor_id=course.instructor_id,
                        batch_id=course.batch_id,
                        session_type=session_type
                    )
                    
                    self.timetable.append(entry)
                    
                    # Update tracking
                    room.occupy_slot(day, time_slot)
                    self.professors[course.instructor_id].assign_slot(day, time_slot)
                    self._mark_batch_busy(course.batch_id, day, time_slot)
                    self.course_daily_count[day_key] = True
                    
                    sessions_scheduled += 1
    
    def _is_batch_free(self, batch_id: str, day: str, slot: str) -> bool:
        """Check if batch is free at given time"""
        key = f"{batch_id}-{day}-{slot}"
        return key not in self.batch_schedule
    
    def _mark_batch_busy(self, batch_id: str, day: str, slot: str):
        """Mark batch as busy"""
        key = f"{batch_id}-{day}-{slot}"
        self.batch_schedule[key] = True
    
    def _is_professor_free(self, prof_id: str, day: str, slot: str) -> bool:
        """Check if professor is free"""
        return self.professors[prof_id].is_available(day, slot)
    
    def _find_available_room(self, day: str, slot: str, room_type: str) -> Room:
        """Find an available room of specified type"""
        for room in self.rooms:
            if room.room_type == room_type and room.is_available(day, slot):
                return room
        return None
    
    def export_to_csv(self, filepath: str):
        """Export timetable to CSV"""
        from utils.csv_handler import CSVHandler
        csv_handler = CSVHandler()
        
        data = [entry.to_dict() for entry in self.timetable]
        csv_handler.write_csv(filepath, data)