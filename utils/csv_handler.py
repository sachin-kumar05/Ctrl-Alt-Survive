import csv
import os
from typing import List, Dict

class CSVHandler:
    """Utility class for CSV operations"""
    
    @staticmethod
    def read_csv(filepath: str) -> List[Dict]:
        """Read CSV file and return list of dictionaries"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        data = []
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        return data
    
    @staticmethod
    def write_csv(filepath: str, data: List[Dict], fieldnames: List[str] = None):
        """Write list of dictionaries to CSV file"""
        if not data:
            print(f"Warning: No data to write to {filepath}")
            return
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if fieldnames is None:
            fieldnames = list(data[0].keys())
        
        with open(filepath, 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Successfully wrote {len(data)} records to {filepath}")