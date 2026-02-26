from src.timetable_scheduler.input_reader import load_courses, load_rooms, load_minors
from src.timetable_scheduler.validator import (
    validate_courses,
    validate_rooms,
    validate_minors,
    validate_room_capacity_for_courses,
)
from src.timetable_scheduler.scheduler import schedule_all
from src.timetable_scheduler.excel_writer import generate_timetables
from src.timetable_scheduler.config import COURSE_FILE, CLASSROOM_FILE, MINOR_FILE


def main():
    print("Running scheduler (non-interactive)\n")
    print(f"Reading: {COURSE_FILE}")
    print(f"Reading: {CLASSROOM_FILE}")
    print(f"Reading: {MINOR_FILE}")

    courses = load_courses()
    rooms = load_rooms()
    minors = load_minors()

    print(f"Loaded {len(courses)} courses, {len(rooms)} rooms, {len(minors)} minors")

    # Validation (collect warnings, but proceed)
    warnings = []
    warnings.extend(validate_courses(courses))
    warnings.extend(validate_rooms(rooms))
    warnings.extend(validate_minors(minors))
    warnings.extend(validate_room_capacity_for_courses(courses, rooms))

    if warnings:
        print("Warnings detected (continuing anyway):")
        for w in warnings:
            print(" -", w)

    print("Starting scheduling...")
    pre, post = schedule_all(courses, rooms, minors)
    print("Scheduling complete. Generating Excel files...")

    generate_timetables(pre.scheduled_classes, courses, rooms)
    generate_timetables(post.scheduled_classes, courses, rooms)

    print("Done. Files written into output/")


if __name__ == '__main__':
    main()
