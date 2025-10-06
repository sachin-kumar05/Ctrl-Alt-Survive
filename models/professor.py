from dataclasses import dataclass, field
from typing import List

@dataclass
class Professor:
    """Professor data model"""
    prof_id: str
    name: str
    department: str = ""
    max_hours_per_week: int = 18
    available_slots: List[str] = field(default_factory=list)
    assigned_courses: List[str] = field(default_factory=list)
    
    def is_available(self, day: str, slot: str) -> bool:
        """Check if professor is available at given time"""
        time_key = f"{day}-{slot}"
        return time_key not in self.assigned_courses
    
    def assign_slot(self, day: str, slot: str):
        """Assign a slot to professor"""
        time_key = f"{day}-{slot}"
        if time_key not in self.assigned_courses:
            self.assigned_courses.append(time_key)