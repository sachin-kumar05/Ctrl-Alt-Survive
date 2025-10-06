from dataclasses import dataclass, field
from typing import List

@dataclass
class Room:
    """Room data model"""
    room_id: str
    capacity: int
    room_type: str  # Lecture, Lab, Seminar
    accessible: bool = False
    occupied_slots: List[str] = field(default_factory=list)
    
    def is_available(self, day: str, slot: str) -> bool:
        """Check if room is available at given time"""
        time_key = f"{day}-{slot}"
        return time_key not in self.occupied_slots
    
    def occupy_slot(self, day: str, slot: str):
        """Mark room as occupied for given slot"""
        time_key = f"{day}-{slot}"
        if time_key not in self.occupied_slots:
            self.occupied_slots.append(time_key)