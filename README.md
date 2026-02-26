# Smart Academic Timetable Generation System

An intelligent, constraint-based scheduling application that automatically generates optimized academic timetables for educational institutions. This system handles complex scheduling requirements including course allocations, room assignments, instructor availability, and specialized time slots for minor programs.

## 📋 Features

- **Automated Timetable Generation**: Intelligently schedules courses across multiple days and time slots
- **Multi-Format Input**: Accepts course, classroom, and minor program data from Excel files
- **Constraint Handling**: Respects multiple constraints:
  - Lunch breaks and non-class time windows
  - Instructor availability
  - Room capacity and facility requirements
  - Separate time windows for minor programs (early morning and evening slots)
  - Lab, lecture, and tutorial duration requirements
  - Sequential class scheduling (batches)
  
- **Dual Interface**:
  - **Web UI**: User-friendly Streamlit interface for interactive scheduling
  - **Command-Line**: Non-interactive mode for automated batch processing
  
- **Excel Output**: Generates detailed timetables in Excel format with color-coded schedules
- **Comprehensive Validation**: Validates input data and reports warnings before scheduling
- **Batch-Based Scheduling**: Handles multiple student batches and course divisions

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AutomatedTimeTable
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- `streamlit` - For the web interface
- `pandas` - For data processing
- `openpyxl` - For Excel file handling
- `pytest` - For running tests (optional)

### Usage

#### Option 1: Web Interface (Interactive)

```bash
streamlit run app.py
```

This opens a browser window with an interactive interface where you can:
1. Upload course data Excel file
2. Upload classroom data Excel file
3. Upload minor program data Excel file
4. Click "Generate Timetable" to schedule
5. Download the generated timetable

#### Option 2: Command-Line (Non-Interactive)

```bash
python run_scheduler_noninteractive.py
```

This mode:
- Reads input files from the `input/` directory
- Runs scheduling without user interaction
- Generates timetable Excel files in the `output/` directory
- Useful for automation and batch processing

## 📁 Project Structure

```
AutomatedTimeTable/
├── app.py                                   # Streamlit web interface
├── run_scheduler_noninteractive.py          # CLI scheduler runner
├── README.md                                # This file
├── requirements.txt                         # Python dependencies
├── input/                                   # Input data directory
│   ├── course_data.xlsx                     # Course information
│   ├── classroom_data.xlsx                  # Classroom/lab information
│   └── minor.xlsx                           # Minor program information
├── output/                                  # Generated timetables
│   ├── pre_semester_timetables.xlsx         # Pre-semester schedule
│   └── post_semester_timetables.xlsx        # Post-semester schedule
└── src/
    └── timetable_scheduler/
        ├── __init__.py
        ├── config.py                        # Configuration and constants
        ├── models.py                        # Data models (Course, Room, etc.)
        ├── input_reader.py                  # Excel file reader
        ├── validator.py                     # Input validation
        ├── scheduler.py                     # Core scheduling algorithm
        ├── room_allocator.py                # Room assignment logic
        └── excel_writer.py                  # Output Excel generation
└── tests/
    ├── test_input_reader.py                 # Input reader unit tests
    ├── test_room_allocator.py               # Room allocator unit tests
    └── test_scheduler.py                    # Scheduler unit tests
```

## 📊 Input File Format

### Course Data (`course_data.xlsx`)

Required columns:
| Column | Type | Description |
|--------|------|-------------|
| Course Code | String | Unique course identifier (e.g., CS101) |
| Course Name | String | Full course name |
| Semester | Integer | Semester level (1-8) |
| Department | String | Department name (e.g., CSE, ECE) |
| LTPSC | String | Format: `L-T-P-S-C` (Lectures, Tutorials, Practicals, Sessions, Contact hours) |
| Credits | Integer | Course credit hours |
| Instructor | String | Instructor name(s), comma-separated if multiple |
| Registered Students | Integer | Number of enrolled students |
| Elective (Yes/No) | String | Whether course is elective |
| Half Semester (Yes/No) | String | Whether course runs half semester |

### Classroom Data (`classroom_data.xlsx`)

Required columns:
| Column | Type | Description |
|--------|------|-------------|
| Room Number | String | Unique room identifier (e.g., A101, LAB01) |
| Type | String | Room type: "Classroom" or "Lab" |
| Capacity | Integer | Maximum student capacity |
| Facilities | String | Available facilities (optional) |

### Minor Program Data (`minor.xlsx`)

Required columns:
| Column | Type | Description |
|--------|------|-------------|
| Program Name | String | Minor program name |
| Registered Students | Integer | Number of students in program |

## ⚙️ Configuration

Edit `src/timetable_scheduler/config.py` to customize:

```python
# Working hours
WORK_START = time(7, 30)      # Day starts at 7:30 AM
WORK_END = time(20, 0)        # Day ends at 8:00 PM

# Minor program time windows (exclusive)
MINOR_WINDOWS = [
    (time(7, 30), time(9, 0)),      # Early morning: 7:30-9:00
    (time(18, 30), time(20, 30)),   # Evening: 6:30-8:30 PM
]

# Regular class window (non-minor)
REGULAR_WINDOW = (time(9, 0), time(18, 30))

# Lunch break
LUNCH_START = time(12, 30)
LUNCH_END = time(14, 0)

# Session durations (in minutes)
TUTORIAL_DURATION = 60
LECTURE_DURATION = 90
LAB_DURATION = 120
MINOR_DURATION = 90

# Minimum gap between classes
GAP_MINUTES = 5
```

## 📤 Output Files

The system generates two Excel files in the `output/` directory:

### 1. Pre-Semester Timetables (`pre_semester_timetables.xlsx`)
- Contains timetables for the first half of courses
- One sheet per batch/section
- Shows day-by-day schedule with:
  - Course code and name
  - Instructor name
  - Room assignment
  - Time slot (color-coded)
  - Lunch breaks (yellow)
  - Free periods (gray)

### 2. Post-Semester Timetables (`post_semester_timetables.xlsx`)
- Contains timetables for the second half of courses
- One sheet per batch/section
- Same format as pre-semester

**Color Coding:**
- Various pastel colors: Regular classes (unique color per cell)
- Yellow: Lunch break
- Light gray: Free periods
- Light blue: Minor program classes

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Run specific test file:
```bash
pytest tests/test_scheduler.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=src/timetable_scheduler
```

## 🔧 Troubleshooting

### Issue: "Missing column in course_data.xlsx"
**Solution**: Verify your Excel file has all required columns with exact names. Check for typos and spaces.

### Issue: "Room capacity insufficient"
**Solution**: Add more rooms to `classroom_data.xlsx` or increase capacities to accommodate registered students.

### Issue: Scheduling takes too long
**Solution**: The algorithm processes large datasets with many constraints. For 500+ courses, scheduling may take several minutes. Consider breaking data into smaller semesters.

### Issue: "Warnings detected" in output
**Solution**: Check the warning messages which indicate potential issues:
- Unscheduled courses
- Instructor conflicts
- Room capacity issues
- Missing data

## 📝 Data Requirements

- **Minimum**: 1 course, 1 classroom, optional minors
- **Typical**: 200-500 courses, 20-50 classrooms
- **Maximum**: Tested with 1000+ courses

## 🎯 Scheduling Algorithm

The system uses a constraint-satisfaction approach:

1. **Input Validation**: Verifies all data integrity
2. **Room Filtering**: Identifies suitable rooms for each course type
3. **Batch Scheduling**: Organizes students into manageable groups
4. **Time Slot Assignment**: Assigns courses to available time slots
5. **Conflict Resolution**: Avoids instructor/room/facility conflicts
6. **Excel Generation**: Creates formatted output files

## 📌 Notes

- Courses marked as "half semester" are scheduled in either pre or post semester
- Multiple instructors for single courses counts each as separate instructor slot
- Lab courses require lab facilities; regular courses use classrooms
- Minor programs have dedicated time windows to minimize conflicts
- The scheduler attempts to find optimal solutions within constraints

## 🤝 Contributing

When contributing to this project:

1. Run existing tests before making changes
2. Add new unit tests for new functionality
3. Follow the existing code style and structure
4. Update this README if adding new features

## 📄 License

This project is designed for educational institution use. Contact the development team for licensing details.

## 📧 Contact & Support

For issues, questions, or suggestions, please reach out to Us.

1. Sachin Kumar [24BCS124]
2. Vanshika Shrivastav [24BCS160]
1. Tejas H [24BCS155]
1. Sidharth Gautam [24BCS145]