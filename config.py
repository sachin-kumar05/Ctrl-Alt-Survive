import os

class Config:
    """Configuration settings for ATESS"""
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INPUT_DIR = os.path.join(BASE_DIR, 'data', 'input')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'data', 'output')
    
    # Time settings
    WORKING_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    TIME_SLOTS = [
        '09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00',
        '14:00-15:00', '15:00-16:00', '16:00-17:00'
    ]
    LUNCH_SLOT = '12:00-13:00'
    
    # Constraints
    MIN_BREAK_HOURS = 3
    MIN_BREAK_MINUTES = 10
    MAX_SESSIONS_PER_DAY = 1  # Per course
    
    # Exam settings
    EXAM_DURATION = 3  # hours
    MIN_SEATS_BETWEEN_SAME_EXAM = 1