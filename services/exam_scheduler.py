from typing import List, Dict
from datetime import datetime, timedelta
from models.course import Course
from models.room import Room
from models.exam import Exam, SeatingPlan
from utils.logger import Logger
from config import Config
import math

class ExamScheduler:
    """Service for scheduling examinations"""
    
    def __init__(self, courses: List[Course], rooms: List[Room], 
                 enrollments: Dict[str, List[str]]):
        self.courses = courses
        self.rooms = rooms
        self.enrollments = enrollments
        self.logger = Logger("ExamScheduler")
        self.exams: List[Exam] = []
        self.seating_plans: List[SeatingPlan] = []
    
    def generate_exam_schedule(self, start_date: str) -> List[Exam]:
        """Generate exam schedule"""
        self.logger.info("Generating exam schedule...")
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        current_date = start_dt
        slot_index = 0
        
        exam_slots = ['09:00-12:00', '14:00-17:00']
        
        for course in self.courses:
            exam_code = f"{course.course_code}-END"
            student_count = len(self.enrollments.get(course.course_code, []))
            
            # Calculate rooms needed
            lecture_rooms = [r for r in self.rooms if r.room_type == 'Lecture']
            rooms_needed = math.ceil(student_count / sum(r.capacity for r in lecture_rooms[:2]))
            assigned_rooms = lecture_rooms[:max(1, rooms_needed)]
            
            exam = Exam(
                exam_code=exam_code,
                course_code=course.course_code,
                course_name=course.course_name,
                date=current_date.strftime('%Y-%m-%d'),
                time_slot=exam_slots[slot_index],
                room_ids=[r.room_id for r in assigned_rooms],
                student_count=student_count,
                invigilator_ids=[course.instructor_id]
            )
            
            self.exams.append(exam)
            
            # Create seating plan
            self._create_seating_plan(exam, assigned_rooms)
            
            # Move to next slot
            slot_index += 1
            if slot_index >= len(exam_slots):
                slot_index = 0
                current_date += timedelta(days=1)
                # Skip weekends
                while current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
        
        self.logger.info(f"Generated {len(self.exams)} exams")
        return self.exams
    
    def _create_seating_plan(self, exam: Exam, rooms: List[Room]):
        """Create seating arrangement for exam"""
        students = self.enrollments.get(exam.course_code, [])
        student_index = 0
        
        for room in rooms:
            seating = SeatingPlan(
                exam_code=exam.exam_code,
                room_id=room.room_id
            )
            
            for seat_num in range(1, room.capacity + 1):
                if student_index < len(students):
                    seating.seat_allocations[seat_num] = students[student_index]
                    student_index += 1
            
            self.seating_plans.append(seating)
    
    def export_exams_to_csv(self, filepath: str):
        """Export exam schedule to CSV"""
        from utils.csv_handler import CSVHandler
        csv_handler = CSVHandler()
        
        data = [exam.to_dict() for exam in self.exams]
        csv_handler.write_csv(filepath, data)
    
    def export_seating_to_csv(self, filepath: str):
        """Export seating plans to CSV"""
        from utils.csv_handler import CSVHandler
        csv_handler = CSVHandler()
        
        data = []
        for plan in self.seating_plans:
            data.extend(plan.to_list())
        
        csv_handler.write_csv(filepath, data)