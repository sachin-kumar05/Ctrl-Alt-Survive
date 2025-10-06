import os
from config import Config
from services.data_loader import DataLoader
from services.timetable_generator import TimetableGenerator
from services.exam_scheduler import ExamScheduler
from utils.logger import Logger

def main():
    """Main entry point for ATESS"""
    logger = Logger("ATESS-Main")
    logger.info("=" * 60)
    logger.info("ATESS - Automated Timetable & Exam Scheduling System")
    logger.info("IIIT Dharwad")
    logger.info("=" * 60)
    
    # Create directories if they don't exist
    os.makedirs(Config.INPUT_DIR, exist_ok=True)
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    # Initialize data loader
    data_loader = DataLoader()
    
    try:
        # Load data from CSV files
        logger.info("\n--- Loading Input Data ---")
        professors = data_loader.load_professors(
            os.path.join(Config.INPUT_DIR, 'professors.csv')
        )
        rooms = data_loader.load_rooms(
            os.path.join(Config.INPUT_DIR, 'rooms.csv')
        )
        courses = data_loader.load_courses(
            os.path.join(Config.INPUT_DIR, 'courses.csv')
        )
        students = data_loader.load_students(
            os.path.join(Config.INPUT_DIR, 'students.csv')
        )
        
        # Convert professors list to dictionary
        prof_dict = {p.prof_id: p for p in professors}
        
        # Generate timetable
        logger.info("\n--- Generating Academic Timetable ---")
        timetable_gen = TimetableGenerator(courses, prof_dict, rooms)
        timetable = timetable_gen.generate()
        
        # Export timetable
        output_file = os.path.join(Config.OUTPUT_DIR, 'timetable.csv')
        timetable_gen.export_to_csv(output_file)
        logger.info(f"Timetable exported to: {output_file}")
        
        # Generate exam schedule
        logger.info("\n--- Generating Exam Schedule ---")
        exam_scheduler = ExamScheduler(courses, rooms, students)
        exams = exam_scheduler.generate_exam_schedule('2025-12-01')
        
        # Export exam schedule
        exam_output = os.path.join(Config.OUTPUT_DIR, 'exam_schedule.csv')
        exam_scheduler.export_exams_to_csv(exam_output)
        logger.info(f"Exam schedule exported to: {exam_output}")
        
        # Export seating plans
        seating_output = os.path.join(Config.OUTPUT_DIR, 'seating_plan.csv')
        exam_scheduler.export_seating_to_csv(seating_output)
        logger.info(f"Seating plan exported to: {seating_output}")
        
        logger.info("\n" + "=" * 60)
        logger.info("ATESS execution completed successfully!")
        logger.info("=" * 60)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error("Please ensure all required CSV files are in the input directory")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()