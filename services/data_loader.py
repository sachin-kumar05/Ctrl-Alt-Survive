from typing import List, Dict
from models.professor import Professor
from models.room import Room
from models.course import Course
from utils.csv_handler import CSVHandler
from utils.logger import Logger

class DataLoader:
    """Service for loading data from CSV files"""
    
    def __init__(self):
        self.logger = Logger("DataLoader")
        self.csv_handler = CSVHandler()
    
    def load_professors(self, filepath: str) -> List[Professor]:
        """Load professors from CSV"""
        self.logger.info(f"Loading professors from {filepath}")
        data = self.csv_handler.read_csv(filepath)
        
        professors = []
        for row in data:
            prof = Professor(
                prof_id=row['prof_id'],
                name=row['name'],
                department=row.get('department', ''),
                max_hours_per_week=int(row.get('max_hours', 18))
            )
            professors.append(prof)
        
        self.logger.info(f"Loaded {len(professors)} professors")
        return professors
    
    def load_rooms(self, filepath: str) -> List[Room]:
        """Load rooms from CSV"""
        self.logger.info(f"Loading rooms from {filepath}")
        data = self.csv_handler.read_csv(filepath)
        
        rooms = []
        for row in data:
            room = Room(
                room_id=row['room_id'],
                capacity=int(row['capacity']),
                room_type=row['type'],
                accessible=row.get('accessible', 'no').lower() == 'yes'
            )
            rooms.append(room)
        
        self.logger.info(f"Loaded {len(rooms)} rooms")
        return rooms
    
    def load_courses(self, filepath: str) -> List[Course]:
        """Load courses from CSV"""
        self.logger.info(f"Loading courses from {filepath}")
        data = self.csv_handler.read_csv(filepath)
        
        courses = []
        for row in data:
            course = Course(
                course_code=row['course_code'],
                course_name=row['course_name'],
                L=int(row['L']),
                T=int(row['T']),
                P=int(row['P']),
                credits=int(row['credits']),
                instructor_id=row['instructor_id'],
                batch_id=row['batch_id']
            )
            courses.append(course)
        
        self.logger.info(f"Loaded {len(courses)} courses")
        return courses
    
    def load_students(self, filepath: str) -> Dict[str, List[str]]:
        """Load student enrollments from CSV"""
        self.logger.info(f"Loading students from {filepath}")
        data = self.csv_handler.read_csv(filepath)
        
        enrollments = {}
        for row in data:
            course_code = row['course_code']
            student_id = row['student_id']
            
            if course_code not in enrollments:
                enrollments[course_code] = []
            enrollments[course_code].append(student_id)
        
        self.logger.info(f"Loaded enrollments for {len(enrollments)} courses")
        return enrollments
