from dataclasses import dataclass

@dataclass
class Course:
    """Course data model"""
    course_code: str
    course_name: str
    L: int  # Lecture hours
    T: int  # Tutorial hours
    P: int  # Practical hours
    credits: int
    instructor_id: str
    batch_id: str
    
    def total_sessions(self) -> int:
        """Calculate total sessions needed"""
        return self.L + self.T
    
    def needs_lab(self) -> bool:
        """Check if course requires lab"""
        return self.P > 0