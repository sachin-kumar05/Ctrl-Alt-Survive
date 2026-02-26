# src/timetable_scheduler/main.py

import sys

from .config import COURSE_FILE, CLASSROOM_FILE, MINOR_FILE
from .input_reader import load_courses, load_rooms, load_minors
from .validator import (
    validate_courses,
    validate_rooms,
    validate_minors,
    validate_room_capacity_for_courses,
    interactive_warning_prompt,
)
from .scheduler import schedule_all
from .excel_writer import generate_timetables


def print_section(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    print_section("Automated Timetable Scheduler (ATS)")
    print("Reading input Excel files from 'input/' ...")

    # ----------------------------
    # LOAD INPUT FILES
    # ----------------------------
    try:
        courses = load_courses()
        rooms = load_rooms()
        minors = load_minors()
    except Exception as e:
        print(f"❌ ERROR: Could not read input files — {e}")
        sys.exit(1)

    print(f"✔ Loaded {len(courses)} courses from {COURSE_FILE}")
    print(f"✔ Loaded {len(rooms)} rooms from {CLASSROOM_FILE}")
    print(f"✔ Loaded {len(minors)} minor programs from {MINOR_FILE}")

    # ----------------------------
    # VALIDATION
    # ----------------------------
    print_section("Validating input data...")

    warnings = []
    warnings.extend(validate_courses(courses))
    warnings.extend(validate_rooms(rooms))
    warnings.extend(validate_minors(minors))
    warnings.extend(validate_room_capacity_for_courses(courses, rooms))

    if not interactive_warning_prompt(warnings):
        print("⚠ Scheduling aborted by user.")
        sys.exit(1)

    # ----------------------------
    # SCHEDULING
    # ----------------------------
    print_section("Starting scheduling (rule-based, constraint solver)...")

    pre_schedule, post_schedule = schedule_all(courses, rooms, minors)

    print("\n✔ Scheduling completed.")

    # ----------------------------
    # OUTPUT WARNINGS
    # ----------------------------
    all_warnings = pre_schedule.warnings + post_schedule.warnings
    if all_warnings:
        print_section("Scheduling Warnings")
        for w in all_warnings:
            print(" -", w)

    # ----------------------------
    # UNSCHEDULED ITEMS
    # ----------------------------
    all_unscheduled = pre_schedule.unscheduled + post_schedule.unscheduled
    if all_unscheduled:
        print_section("Unscheduled Items")
        for u in all_unscheduled:
            print(" -", u)

    # ----------------------------
    # EXCEL GENERATION
    # ----------------------------
    print_section("Generating Excel Timetables (into 'output/' folder)")

    try:
        generate_timetables(pre_schedule.scheduled_classes, courses, rooms)
        generate_timetables(post_schedule.scheduled_classes, courses, rooms)
    except Exception as e:
        print(f"❌ ERROR while generating Excel files — {e}")
        sys.exit(1)

    print("\n✔ All done! Your final timetables are available in the 'output/' folder.\n")


if __name__ == "__main__":
    main()
