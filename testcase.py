import unittest
import os
import csv
import shutil
from collections import namedtuple

# --- MOCK REQUIRED IMPORTS ---
Professor = namedtuple('Professor', 'prof_id, name, max_hours')
Room = namedtuple('Room', 'room_id, capacity, type')
Course = namedtuple('Course', 'code, title, L, T, P, credits, instructor_id, room_no, lab_room_no')
Student = namedtuple('Student', 'course_code, student_id') 

class MockConfig:
    INPUT_DIR = 'data/input'
    OUTPUT_DIR = 'data/output'

class MockDataLoader:
    
    def __init__(self, config):
        self.config = config

    def _parse_l_t_p_s_c(self, ltp_str):
        """Helper to parse L-T-P-S-C string."""
        try:
            parts = ltp_str.split('-')
            l, t, p = map(lambda x: int(x) if x and x.strip().isdigit() else 0, parts[:3])
            c = int(parts[4]) if len(parts) > 4 and parts[4].strip().isdigit() else 0
            return l, t, p, c
        except Exception:
            return 0, 0, 0, 0

    def load_courses(self, full_filepath):
        """Loads and converts course data from the uploaded semester CSVs."""
        courses_list = []
        try:
            with open(full_filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row.get('COURSE CODE') or row.get('COURSE_CODE', '')
                    title = row.get('COURSE TITLE') or row.get('COURSE_TITLE', '')
                    ltpsc = row.get('L-T-P-S-C', '0-0-0-0-0')
                    faculty = row.get('Faculty', 'TBD')
                    room_no = row.get('Room.No') or row.get('Room No.', '')
                    lab_room_no = row.get('Lab Room. No') or row.get('Lab Room NO.', '')
                    
                    L, T, P, credits = self._parse_l_t_p_s_c(ltpsc)
                    
                    instructor_id = 'PROF_' + faculty.split()[1].replace('.', '') if len(faculty.split()) > 1 else 'PROF_UNKNOWN'

                    if not code or not title:
                        continue

                    courses_list.append(Course(
                        code=code.strip(), 
                        title=title.replace('\n', ' ').strip(), 
                        L=L, 
                        T=T, 
                        P=P, 
                        credits=credits, 
                        instructor_id=instructor_id,
                        room_no=room_no.strip(),
                        lab_room_no=lab_room_no.strip()
                    ))
            return courses_list
        except FileNotFoundError:
            raise
        except Exception as e:
            raise ValueError(f"Data loading failed in {full_filepath}: {e}")

class TestATESSDataLoader(unittest.TestCase):
    
    # Static data for expected counts
    _EXPECTED_COUNTS = {
        '1st_sem_data.csv': 15,
        '3rd_sem_data.csv': 17,
        '5th_sem_data.csv': 13,
        '7th_sem_data.csv': 12
    }
    
    def setUp(self):
        # 1. Guaranteed Dictionary Initialization (Fixes the AttributeError)
        self.FILE_MAPPING = {
            '1st sem.xlsx - 1st_sem_data.csv',
            '3rd sem.xlsx - 3rd_sem_data.csv',
            '5th sem.xlsx - 5th_sem_data.csv',
            '7th sem.xlsx - 7th_sem_data.csv',
        }
        self.EXPECTED_COUNTS = self._EXPECTED_COUNTS

        self.config = MockConfig()
        self.data_loader = MockDataLoader(self.config)
        self.input_dir = self.config.INPUT_DIR
        self.missing_file = 'non_existent_file.csv'
        
        os.makedirs(self.input_dir, exist_ok=True)
        
        # 2. File Check and Copy
        for original_name, target_name in self.FILE_MAPPING.items():
            if not os.path.exists(original_name):
                # The final check for file presence in the execution directory
                raise FileNotFoundError(
                    f"TEST SETUP ERROR: Cannot find the original file '{original_name}'. "
                    "You must place this file in the same directory as the test script."
                )
            
            shutil.copy(original_name, os.path.join(self.input_dir, target_name))

    def tearDown(self):
        if os.path.exists(self.input_dir):
            shutil.rmtree(self.input_dir)

    def _get_courses(self, original_name):
        """Helper to get courses for a specific file."""
        filepath = self.FILE_MAPPING[original_name]
        full_filepath = os.path.join(self.input_dir, filepath) 
        return self.data_loader.load_courses(full_filepath), filepath

    def test_tc_sv_01_load_1st_sem_data(self):
        courses, filepath = self._get_courses('1st sem.xlsx - Sheet1.csv')
        self.assertEqual(len(courses), self.EXPECTED_COUNTS[filepath])
        cs161 = next(c for c in courses if c.code == 'CS161')
        self.assertEqual(cs161.L, 3)
        self.assertEqual(cs161.credits, 4)

    def test_tc_sv_02_load_3rd_sem_data(self):
        courses, filepath = self._get_courses('3rd sem.xlsx - Sheet1.csv')
        self.assertEqual(len(courses), self.EXPECTED_COUNTS[filepath])
        ma262 = next(c for c in courses if c.code == 'MA262')
        self.assertEqual(ma262.L, 3)
        self.assertEqual(ma262.credits, 2)
    
    def test_tc_sv_03_load_5th_sem_data(self):
        courses, filepath = self._get_courses('5th sem.xlsx - Sheet1.csv')
        self.assertEqual(len(courses), self.EXPECTED_COUNTS[filepath])
        ds302 = next(c for c in courses if c.code == 'DS302')
        self.assertIn('Computer Communication Networks', ds302.title)
        self.assertEqual(ds302.P, 2)
        self.assertEqual(ds302.credits, 5)

    def test_tc_sv_04_load_7th_sem_data(self):
        courses, filepath = self._get_courses('7th sem.xlsx - Sheet1.csv')
        self.assertEqual(len(courses), self.EXPECTED_COUNTS[filepath])
        ec456 = next(c for c in courses if c.code == 'EC456')
        self.assertEqual(ec456.L, 3)
        self.assertEqual(ec456.credits, 4)

    def test_tc_sv_05_file_not_found(self):
        full_filepath = os.path.join(self.input_dir, self.missing_file)
        with self.assertRaises(FileNotFoundError) as context:
            self.data_loader.load_courses(full_filepath)
        self.assertIn(self.missing_file, str(context.exception))
        
    def test_tc_sv_06_r2_course_hours_validation(self):
        temp_filepath = os.path.join(self.input_dir, 'bad_course.csv')
        header = ['elective or not', 'fullsem or halfsem', 'COURSE CODE', 'COURSE TITLE', 'Faculty', 'Class Assisstants', 'Lab Assisstants', 'L-T-P-S-C', 'Room.No', 'Lab Room. No']
        mock_data = [
            ['NO', 'fullsem', 'BAD101', 'Bad Course', 'Dr. X', '-', '-', '3-1-A-0-', 'C101', '-'] 
        ]
        
        with open(temp_filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(mock_data)
        
        courses = self.data_loader.load_courses(temp_filepath)
        bad_course = courses[0]
        
        self.assertEqual(bad_course.P, 0)
        self.assertEqual(bad_course.credits, 0)
        
        os.remove(temp_filepath)

if __name__ == '__main__':
    os.makedirs(MockConfig.INPUT_DIR, exist_ok=True)
    print("--- Running ATESS Data Loader Validation Test Suite ---")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    print("--- Test Run Complete ---")