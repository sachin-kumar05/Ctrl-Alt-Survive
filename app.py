import streamlit as st
import os
import shutil
import tempfile

from src.timetable_scheduler.input_reader import load_courses, load_rooms, load_minors
from src.timetable_scheduler.validator import (
    validate_courses,
    validate_rooms,
    validate_minors,
    validate_room_capacity_for_courses,
)
from src.timetable_scheduler.scheduler import schedule_all
from src.timetable_scheduler.excel_writer import generate_timetables
from src.timetable_scheduler import config

st.set_page_config(page_title="Smart Academic Timetable", layout="wide")

st.title("📅 Smart Academic Timetable Generation System")

st.sidebar.header("Upload Required Files")

course_file = st.sidebar.file_uploader("Upload Course File", type=["csv", "xlsx"])
room_file = st.sidebar.file_uploader("Upload Classroom File", type=["csv", "xlsx"])
minor_file = st.sidebar.file_uploader("Upload Minor File", type=["csv", "xlsx"])

if st.sidebar.button("Generate Timetable"):

    if not course_file or not room_file or not minor_file:
        st.error("Please upload all required files.")
    else:
        with tempfile.TemporaryDirectory() as tmpdir:

            input_dir = os.path.join(tmpdir, "input")
            output_dir = os.path.join(tmpdir, "output")

            os.makedirs(input_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)

            # Save uploaded files
            course_path = os.path.join(input_dir, "courses.xlsx")
            room_path = os.path.join(input_dir, "rooms.xlsx")
            minor_path = os.path.join(input_dir, "minors.xlsx")

            with open(course_path, "wb") as f:
                f.write(course_file.getbuffer())

            with open(room_path, "wb") as f:
                f.write(room_file.getbuffer())

            with open(minor_path, "wb") as f:
                f.write(minor_file.getbuffer())

            # Override config paths
            config.COURSE_FILE = course_path
            config.CLASSROOM_FILE = room_path
            config.MINOR_FILE = minor_path

            st.info("Loading data...")

            courses = load_courses()
            rooms = load_rooms()
            minors = load_minors()

            warnings = []
            warnings.extend(validate_courses(courses))
            warnings.extend(validate_rooms(rooms))
            warnings.extend(validate_minors(minors))
            warnings.extend(validate_room_capacity_for_courses(courses, rooms))

            if warnings:
                st.warning("Validation Warnings:")
                for w in warnings:
                    st.write("•", w)

            st.info("Scheduling in progress...")

            pre, post = schedule_all(courses, rooms, minors)

            generate_timetables(pre.scheduled_classes, courses, rooms)
            generate_timetables(post.scheduled_classes, courses, rooms)

            st.success("Timetable generated successfully!")

            # Zip output files
            zip_path = os.path.join(tmpdir, "timetable_output.zip")
            shutil.make_archive(zip_path.replace(".zip", ""), 'zip', "output")

            with open(zip_path, "rb") as f:
                st.download_button(
                    "Download Timetable Files",
                    f,
                    file_name="timetable_output.zip"
                )
