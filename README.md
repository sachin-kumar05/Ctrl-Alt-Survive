# ATESS - Automated Timetable and Exam Scheduling System

## 📚 Overview

**ATESS** (Automated Timetable and Exam Scheduling System) is a comprehensive Python-based solution designed for **IIIT Dharwad** to automate the generation of academic timetables, exam schedules, and seating arrangements.

This is the **CSV-only version** - no external dependencies required! Perfect for:
- ✅ Quick deployment without installations
- ✅ Maximum compatibility across systems
- ✅ Lightweight and fast execution

---

## ✨ Features

### Academic Timetable Generation
- ✅ **R1**: Real-time resource availability tracking (professors, rooms, batches)
- ✅ **R2**: Course details validation and acceptance
- ✅ **R3**: Self-study hour allocation for each batch
- ✅ **R4**: Minimum 3-hour breaks between professor sessions
- ✅ **R5**: Maximum one lecture/tutorial per course per day
- ✅ **R6**: 10-minute breaks between consecutive sessions
- ✅ **R7**: Class rescheduling support
- ✅ **R8**: Automatic lunch break scheduling
- ✅ **R9**: Structured, readable timetable output
- ✅ **R10**: Lab scheduling aligned with lectures
- ✅ **R12**: Course grouping into slot baskets

### Examination Scheduling
- ✅ **R13**: Automated exam timetable and seating arrangements
- ✅ **R14**: Accessibility and special needs accommodation
- ✅ **R15**: Fair invigilator allocation

### System Capabilities
- 🚀 Conflict-free scheduling
- 📊 CSV-based input/output
- 🔄 Easy data import/export
- 📝 Comprehensive logging
- ⚡ Fast execution (pure Python)
- 🎯 Zero external dependencies

---

## 📋 Requirements

- **Python**: 3.8 or higher
- **Dependencies**: None! (Uses Python standard library only)
---

## 📁 Project Structure

```
atess_project/
├── main.py                      # Main entry point
├── config.py                    # System configuration
├── README.md                    # This file
├── requirements.txt             # Empty (no dependencies!)
│
├── models/                      # Data models
│   ├── __init__.py
│   ├── professor.py            # Professor data model
│   ├── room.py                 # Room data model
│   ├── course.py               # Course data model
│   ├── timetable.py            # Timetable entry model
│   └── exam.py                 # Exam and seating models
│
├── services/                    # Business logic
│   ├── __init__.py
│   ├── data_loader.py          # Load data from CSV
│   ├── timetable_generator.py  # Generate timetables
│   ├── exam_scheduler.py       # Schedule exams
│   └── validator.py            # Validate constraints
│
├── utils/                       # Utilities
│   ├── __init__.py
│   ├── csv_handler.py          # CSV read/write operations
│   └── logger.py               # Logging utility
│
└── data/
    ├── input/                   # Input CSV files (you provide)
    │   ├── professors.csv
    │   ├── rooms.csv
    │   ├── courses.csv
    │   └── students.csv
    │
    └── output/                  # Generated CSV files
        ├── timetable.csv
        ├── exam_schedule.csv
        └── seating_plan.csv
```

---

## 📊 Input CSV Format

### 1. professors.csv

```csv
prof_id,name,department,max_hours
PROF001,Dr. Vivekraj,Computer Science,18
PROF002,Dr. Sharma,Mathematics,18
PROF003,Dr. Kumar,Electronics,18
```

**Columns:**
- `prof_id`: Unique professor identifier
- `name`: Professor's full name
- `department`: Department name
- `max_hours`: Maximum teaching hours per week (default: 18)

---

### 2. rooms.csv

```csv
room_id,capacity,type,accessible
R101,60,Lecture,yes
R102,40,Lecture,no
L201,30,Lab,yes
S301,100,Seminar,yes
```

**Columns:**
- `room_id`: Unique room identifier
- `capacity`: Number of seats
- `type`: Room type (Lecture, Lab, Seminar)
- `accessible`: Accessibility features (yes/no)

---

### 3. courses.csv

```csv
course_code,course_name,L,T,P,credits,instructor_id,batch_id
CS301,Data Structures,3,1,2,4,PROF001,3CSE-A
CS302,Algorithms,3,1,0,4,PROF002,3CSE-A
MA201,Discrete Mathematics,3,1,0,4,PROF003,3CSE-A
```

**Columns:**
- `course_code`: Unique course code
- `course_name`: Full course name
- `L`: Lecture hours per week
- `T`: Tutorial hours per week
- `P`: Practical/Lab hours per week
- `credits`: Course credits
- `instructor_id`: Professor ID (must match professors.csv)
- `batch_id`: Student batch identifier

---

### 4. students.csv

```csv
course_code,student_id
CS301,24BCS001
CS301,24BCS002
CS301,24BCS003
CS302,24BCS001
CS302,24BCS002
```

**Columns:**
- `course_code`: Course code (must match courses.csv)
- `student_id`: Unique student identifier

**Note:** One row per student per course enrollment

---

## 📤 Output CSV Format

### 1. timetable.csv

```csv
slot_id,day,time_slot,course_code,course_name,room_id,instructor_id,batch_id,session_type
CS301-0,Monday,09:00-10:00,CS301,Data Structures,R101,PROF001,3CSE-A,Lecture
CS301-1,Monday,10:00-11:00,CS301,Data Structures,R101,PROF001,3CSE-A,Lecture
```

**Generated columns:**
- `slot_id`: Unique slot identifier
- `day`: Day of week
- `time_slot`: Time range
- `course_code`: Course code
- `course_name`: Course name
- `room_id`: Allocated room
- `instructor_id`: Professor teaching
- `batch_id`: Student batch
- `session_type`: Lecture, Tutorial, Lab, or Self-Study

---

### 2. exam_schedule.csv

```csv
exam_code,course_code,course_name,date,time_slot,rooms,student_count,invigilators
CS301-END,CS301,Data Structures,2025-12-01,09:00-12:00,"R101,R102",50,PROF001
CS302-END,CS302,Algorithms,2025-12-01,14:00-17:00,R101,48,PROF002
```

**Generated columns:**
- `exam_code`: Unique exam identifier
- `course_code`: Course code
- `course_name`: Course name
- `date`: Exam date (YYYY-MM-DD)
- `time_slot`: Exam time range
- `rooms`: Allocated rooms (comma-separated)
- `student_count`: Number of students
- `invigilators`: Assigned faculty (comma-separated)

---

### 3. seating_plan.csv

```csv
exam_code,room_id,seat_number,student_id
CS301-END,R101,1,24BCS001
CS301-END,R101,2,24BCS002
CS301-END,R101,3,24BCS003
```

**Generated columns:**
- `exam_code`: Exam identifier
- `room_id`: Room where student is seated
- `seat_number`: Seat number
- `student_id`: Student identifier

---

## 📄 License

This software is developed for **IIIT Dharwad** as part of the academic project:
- **Project**: Ctrl+Alt+Survive6
- **Course**: Software Engineering
- **Guide**: Dr. Vivekraj
- **Team**: Tejas H, Siddharth Gautam, Sachin Kumar, Vanshika Shrivastava

---


*Last Updated: October 2025*  
*Version: 1.0 (CSV Edition)*  
*Institution: IIIT Dharwad*