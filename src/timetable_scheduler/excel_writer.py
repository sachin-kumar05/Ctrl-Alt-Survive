# ============================================
# excel_writer.py  (UPDATED – PART 1/4)
# ============================================

from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from pathlib import Path
import sys

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Alignment, Font

from .models import ScheduledClass, Course, Room
from .config import (
    OUTPUT_DIR,
    DAYS,
    WORK_START,
    WORK_END,
    LUNCH_START,
    LUNCH_END,
    time_to_minutes,
    format_time_range,
    GAP_MINUTES,
)

# ----------------------------------------------------
# COLORS
# ----------------------------------------------------

BREAK_COLOR = "D9D9D9"      # Light gray
LUNCH_COLOR = "FFD966"      # Yellow
MINOR_COLOR = "C9DAF8"      # Light blue


def build_color_palette():
    """
    Palette for normal class cells.
    We must give each CELL a unique color (not each course).
    """
    return [
        "FFC7CE", "C6EFCE", "FFEB9C", "BDD7EE",
        "F8CBAD", "D9D2E9", "DDEBF7", "E2EFDA",
        "FFF2CC", "F4B084", "D6DCE4", "C5E0B4",
        "FFD966", "9BC2E6", "8FAADC", "F2DCDB",
        "D9E1F2", "E4DFEC", "EDEDED"
    ]


def overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    """Time-interval overlap check."""
    return not (a_end <= b_start or b_end <= a_start)


# ----------------------------------------------------
# PARSE BATCH ID
# ----------------------------------------------------

def parse_batch_id(batch_id: str) -> Tuple[str, int, str]:
    """
    Parse:  CSE_SEM3_SECA → (CSE, 3, A)
    """
    parts = batch_id.split("_")
    dept = parts[0]
    sem = 0
    section = ""

    if len(parts) >= 2 and parts[1].upper().startswith("SEM"):
        try:
            sem = int(parts[1][3:])
        except:
            sem = 0

    if len(parts) >= 3 and parts[2].upper().startswith("SEC"):
        section = parts[2][3:]

    return dept, sem, section


# ----------------------------------------------------
# BUILD DAY SLOTS (TIME-SPLITTING ENGINE)
# ----------------------------------------------------

def build_day_slots_for_batch(
    classes: List[ScheduledClass],
    work_start_min: int,
    work_end_min: int,
    lunch_start_min: int,
    lunch_end_min: int,
):
    """
    Convert scheduled classes → time slots for a single day.
    Handles:
      - class
      - break (15min between 2 classes)
      - lunch
      - empty ignored
    """
    day_classes: Dict[int, List[ScheduledClass]] = defaultdict(list)
    for sc in classes:
        day_classes[sc.day_index].append(sc)

    per_day_slots = {}

    for day_index in range(len(DAYS)):
        cls_list = day_classes.get(day_index, [])
        if not cls_list:
            per_day_slots[day_index] = []
            continue

        # Build boundary timestamps
        boundaries = {
            work_start_min,
            work_end_min,
            lunch_start_min,
            lunch_end_min,
        }
        for sc in cls_list:
            s = sc.start_minute
            e = sc.start_minute + sc.duration
            boundaries.add(max(work_start_min, s))
            boundaries.add(min(work_end_min, e))

        boundaries = sorted(boundaries)

        # Convert boundaries → intervals
        raw_intervals = []
        for i in range(len(boundaries) - 1):
            s = boundaries[i]
            e = boundaries[i + 1]
            if e > s:
                raw_intervals.append((s, e))

        slots = []

        # For checking break conditions
        class_starts = {sc.start_minute for sc in cls_list}
        class_ends = {sc.start_minute + sc.duration for sc in cls_list}

        def find_exact_class(s, e):
            for sc in cls_list:
                if sc.start_minute == s and sc.start_minute + sc.duration == e:
                    return sc
            return None

        for idx, (s, e) in enumerate(raw_intervals):
            if e <= work_start_min or s >= work_end_min:
                continue

            s = max(s, work_start_min)
            e = min(e, work_end_min)
            if e <= s:
                continue

            sc = find_exact_class(s, e)
            if sc:
                slots.append({
                    "start": s,
                    "end": e,
                    "kind": "class",
                    "sc": sc
                })
                continue

            # LUNCH
            if overlaps(s, e, lunch_start_min, lunch_end_min):
                slots.append({
                    "start": s,
                    "end": e,
                    "kind": "lunch",
                    "sc": None
                })
                continue

            # BREAK (only if EXACT 15min + flanked by classes)
            if (e - s) == GAP_MINUTES:
                prev_is_class = s in class_ends
                next_is_class = e in class_starts
                touching_lunch = (e == lunch_start_min) or (s == lunch_end_min)
                last_interval = idx == len(raw_intervals) - 1

                if prev_is_class and next_is_class and not touching_lunch and not last_interval:
                    slots.append({
                        "start": s,
                        "end": e,
                        "kind": "break",
                        "sc": None,
                    })
                    continue

            # empty → DO NOTHING

        per_day_slots[day_index] = slots

    return per_day_slots


# ----------------------------------------------------
# DETERMINE ELECTIVE BASKET
# (Used for the new legend table)
# ----------------------------------------------------

def determine_basket_for_course(course: Course) -> str:
    sem = course.semester
    cr = course.credits

    if sem == 1:
        return "elective basket 1.1" if cr == 1 else "elective basket 1.2"

    if sem == 3:
        return "elective basket 3.1" if cr == 1 else "elective basket 3.2"

    if sem == 5:
        return "elective basket 5.1"

    if sem == 7:
        # stable pseudo-round-robin
        part = (abs(hash(course.code)) % 4) + 1
        return f"elective basket 7.{part}"

    return f"elective basket {sem}.1"
# -----------------------------------------
# PART 2/4 — parent_batch_id + generate_timetables
# -----------------------------------------

def parent_batch_id(batch_id: str) -> str:
    """
    If batch_id ends with -G1 or -G2 return parent (strip suffix),
    otherwise return batch_id unchanged.
    """
    if batch_id.endswith("-G1") or batch_id.endswith("-G2"):
        return batch_id.rsplit("-", 1)[0]
    return batch_id


def generate_timetables(
    scheduled: List[ScheduledClass],
    courses: List[Course],
    rooms: List[Room],
):
    """
    Generate Excel workbooks per department with one file per term:
      {DEPT}_PreMid.xlsx and {DEPT}_PostMid.xlsx

    Each workbook contains sheets per parent-batch (e.g., CSE-A Sem3).
    This function merges lab group rows (G1/G2) back into parent batch display
    by detecting labs at the same start/end and combining them into one cell.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    course_map: Dict[str, Course] = {c.code: c for c in courses}

    if not scheduled:
        print("No scheduled classes to write.")
        return

    # Determine term label (assume scheduled contains only one term per call)
    terms_present = {sc.term for sc in scheduled}
    term_raw = next(iter(terms_present)) if terms_present else "PRE"
    term_label = "PreMid" if term_raw == "PRE" else ("PostMid" if term_raw == "POST" else term_raw)

    # Group classes by PARENT batch id (merge -G1/-G2 back to parent)
    batch_classes: Dict[str, List[ScheduledClass]] = defaultdict(list)
    batch_meta: Dict[str, Tuple[str, int, str]] = {}

    for sc in scheduled:
        parent = parent_batch_id(sc.batch_id)
        batch_classes[parent].append(sc)
        if parent not in batch_meta:
            batch_meta[parent] = parse_batch_id(parent)

    # Group parent batches by department
    dept_batches: Dict[str, List[str]] = defaultdict(list)
    for batch_id, (dept, _sem, _sec) in batch_meta.items():
        dept_batches[dept].append(batch_id)

    palette = build_color_palette()

    work_start_min = time_to_minutes(WORK_START)
    work_end_min = time_to_minutes(WORK_END)
    lunch_start_min = time_to_minutes(LUNCH_START)
    lunch_end_min = time_to_minutes(LUNCH_END)

    # Build global room occupancy map (for elective legend allocation)
    room_occupancy: Dict[str, List[Tuple[int, int, int]]] = defaultdict(list)
    for sc in scheduled:
        if sc.room_number:
            room_occupancy[sc.room_number].append((sc.day_index, sc.start_minute, sc.start_minute + sc.duration))

    for dept, batches in dept_batches.items():
        if not batches:
            continue

        wb = Workbook()
        first_sheet_created = False

        def batch_sort_key(bid: str):
            d, sem, sec = batch_meta[bid]
            return (sem, 0 if sec else 1, sec)

        for batch_id in sorted(batches, key=batch_sort_key):
            dept_b, sem_b, sec_b = batch_meta[batch_id]
            if dept_b != dept:
                continue

            classes_for_parent = batch_classes.get(batch_id, [])
            if not classes_for_parent:
                continue

            # Build per-day slots (this function uses exact class matches)
            per_day_slots = build_day_slots_for_batch(
                classes_for_parent,
                work_start_min,
                work_end_min,
                lunch_start_min,
                lunch_end_min,
            )

            max_slots = max((len(slots) for slots in per_day_slots.values()), default=0)

            # sheet name
            if sec_b:
                sheet_name = f"{dept}-{sec_b} Sem{sem_b}"
            else:
                sheet_name = f"{dept} Sem{sem_b}"

            if not first_sheet_created:
                ws = wb.active
                ws.title = sheet_name
                first_sheet_created = True
            else:
                ws = wb.create_sheet(title=sheet_name)

            # Title row
            ws["A1"] = f"Batch: {batch_id} | Term: {term_label}"
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_slots + 1)
            ws["A1"].alignment = Alignment(horizontal="center")
            ws["A1"].font = Font(bold=True)

            # Header row
            ws["A2"] = "Day"
            ws["A2"].font = Font(bold=True)
            for i in range(max_slots):
                cell = ws.cell(row=2, column=2 + i)
                cell.value = f"Slot {i+1}"
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")

            # Precompute lab map for parent: (day, start, end) -> list of lab scs
            labs_map: Dict[Tuple[int, int, int], List[ScheduledClass]] = defaultdict(list)
            for sc in classes_for_parent:
                if sc.is_lab:
                    key = (sc.day_index, sc.start_minute, sc.start_minute + sc.duration)
                    labs_map[key].append(sc)

            # Write rows: days
            row = 3
            for day_index, day_name in enumerate(DAYS):
                ws.cell(row=row, column=1).value = day_name
                day_slots = per_day_slots.get(day_index, [])

                for i, slot in enumerate(day_slots):
                    col = 2 + i
                    cell = ws.cell(row=row, column=col)

                    s = slot["start"]
                    e = slot["end"]
                    kind = slot["kind"]
                    time_label = format_time_range(s, e)

                    if kind == "class":
                        # FIRST: check if labs exist exactly at this (day,s,e) — if so merge and display lab format
                        lm_key = (day_index, s, e)
                        lab_sc_list = labs_map.get(lm_key, [])

                        if lab_sc_list:
                            # Build lab display (Format A) — ensure exactly one room per group and no duplicates
                            course_code = lab_sc_list[0].course_code if lab_sc_list[0].course_code else "LAB"

                            # Map group -> room (only keep first seen room per group)
                            group_rooms = {}  # e.g. {'G1': 'L105', 'G2': 'L106'}
                            for lsc in lab_sc_list:
                                # determine group suffix reliably
                                if lsc.batch_id.endswith("-G1"):
                                    g = "G1"
                                elif lsc.batch_id.endswith("-G2"):
                                    g = "G2"
                                else:
                                    # fallback: derive from batch_id last token
                                    parts = lsc.batch_id.rsplit("-", 1)
                                    g = parts[-1] if len(parts) > 1 else "G?"
                                # only set room once per group (avoid duplicates)
                                if g not in group_rooms:
                                    group_rooms[g] = lsc.room_number or "TBA"

                            # order output: G1 then G2 (if present)
                            parts = []
                            for g in ("G1", "G2"):
                                if g in group_rooms:
                                    parts.append(f"{g}-{group_rooms[g]}")
                            # if neither G1 nor G2 present, include any single group's info
                            if not parts:
                                # pick available groups deterministically
                                for g, rm in sorted(group_rooms.items()):
                                    parts.append(f"{g}-{rm}")

                            rooms_line = " | ".join(parts) if parts else "TBA"

                            # Final cell value: time + course-LAB + rooms
                            cell.value = f"{time_label}\n{course_code}-LAB\n{rooms_line}"

                            # Lab cell: do NOT show instructor
                            slot_color = build_color_palette()[(row + col) % len(build_color_palette())]
                            cell.fill = PatternFill(start_color=slot_color, end_color=slot_color, fill_type="solid")

                        else:
                            sc = slot.get("sc")
                            if sc and sc.is_minor:
                                # Minor slot — must display time + "Minor"
                                cell.value = f"{time_label}\nMinor"
                                cell.fill = PatternFill(start_color=MINOR_COLOR, end_color=MINOR_COLOR, fill_type="solid")
                            elif sc:
                                # Handle ELECTIVE BASKET SLOTS (do not print TBA lines in timetable cell)
                                is_basket = False
                                if isinstance(sc.course_code, str):
                                    low = sc.course_code.lower()
                                    if low.startswith("elective basket") or low.startswith("open elective") or ("elective" in low and "basket" in low):
                                        is_basket = True
                                if is_basket:
                                    # If tutorial basket:
                                    if sc.is_tutorial:
                                        label = f"{sc.course_code}-TUT"
                                    else:
                                        label = sc.course_code
                                    cell.value = f"{time_label}\n{label}"
                                    # give basket slot a neutral color (reuse palette)
                                    slot_color = build_color_palette()[(row + col) % len(build_color_palette())]
                                    cell.fill = PatternFill(start_color=slot_color, end_color=slot_color, fill_type="solid")
                                else:
                                    # Normal class or tutorial (non-basket)
                                    if sc.is_tutorial:
                                        # COURSE-TUT + room + instructor
                                        cell.value = f"{time_label}\n{sc.course_code}-TUT\n{sc.room_number or 'TBA'}\n{sc.instructor or 'TBA'}"
                                    else:
                                        # Lecture: time + course + room + instructor
                                        cell.value = f"{time_label}\n{sc.course_code or ''}\n{sc.room_number or 'TBA'}\n{sc.instructor or 'TBA'}"

                                    # give unique color per class cell (except breaks/lunch/minor)
                                    slot_color = build_color_palette()[(row + col) % len(build_color_palette())]
                                    cell.fill = PatternFill(start_color=slot_color, end_color=slot_color, fill_type="solid")
                            else:
                                # safety fallback
                                cell.value = ""

                    elif kind == "break":
                        cell.value = f"{time_label}\nBreak"
                        cell.fill = PatternFill(start_color=BREAK_COLOR, end_color=BREAK_COLOR, fill_type="solid")
                    elif kind == "lunch":
                        cell.value = f"{time_label}\nLunch break"
                        cell.fill = PatternFill(start_color=LUNCH_COLOR, end_color=LUNCH_COLOR, fill_type="solid")

                    cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")

                row += 1

            # --------------------
            # Legend: Non-Elective
            # --------------------
            legend_start = row + 2
            ws.cell(row=legend_start, column=1).value = "Legend - Non-Elective Courses"
            ws.cell(row=legend_start, column=1).font = Font(bold=True)
            legend_row = legend_start + 1

            ws.cell(legend_row, column=1).value = "Course Code"
            ws.cell(legend_row, column=2).value = "Course Name"
            ws.cell(legend_row, column=3).value = "Faculty"
            for c in range(1, 4):
                ws.cell(legend_row, column=c).font = Font(bold=True)
            legend_row += 1

            used_codes = {
                sc.course_code
                for sc in classes_for_parent
                if sc.course_code and sc.course_code in course_map
            }
            non_electives = [code for code in used_codes if not course_map[code].is_elective]
            electives_in_timetable = [code for code in used_codes if course_map[code].is_elective]

            for code in sorted(non_electives):
                cobj = course_map[code]
                ws.cell(legend_row, column=1).value = code
                ws.cell(legend_row, column=2).value = cobj.name
                ws.cell(legend_row, column=3).value = ", ".join(cobj.instructors)
                legend_row += 1

            # --------------------
            # Legend: Elective (Basket | Course | Instructor | Room)
            # --------------------
            legend_row += 1
            ws.cell(legend_row, column=1).value = "Legend - Elective Courses (Basket | Course Code | Instructor | Room)"
            ws.cell(legend_row, column=1).font = Font(bold=True)
            legend_row += 1

            ws.cell(legend_row, column=1).value = "Basket"
            ws.cell(legend_row, column=2).value = "Elective Course Code"
            ws.cell(legend_row, column=3).value = "Instructor"
            ws.cell(legend_row, column=4).value = "Room"
            for c in range(1, 5):
                ws.cell(legend_row, column=c).font = Font(bold=True)
            legend_row += 1

            # Build electives for this semester/dept
            sem_courses = [c for c in courses if c.semester == sem_b and c.department == dept]
            electives_for_sem = [c for c in sem_courses if c.is_elective]
            grouped = defaultdict(list)
            for c in electives_for_sem:
                basket = determine_basket_for_course(c)
                # Map default basket names into Open Elective names for sem 1/3/5
                low = basket.lower()
                if low.startswith("elective basket 1") or low.startswith("elective basket 1."):
                    basket = "Open Elective-1"
                elif low.startswith("elective basket 3"):
                    basket = "Open Elective-3"
                elif low.startswith("elective basket 5"):
                    basket = "Open Elective-5"
                grouped[basket].append(c)

            rooms_sorted = sorted(rooms, key=lambda r: r.capacity)

            # We'll try to allocate rooms in legend per-course ensuring capacity fit (best-effort)
            for basket in sorted(grouped.keys()):
                courses_in_basket = sorted(grouped[basket], key=lambda x: x.code)
                used_rooms_this_basket = set()
                for c in courses_in_basket:
                    need = c.registered_students or 0
                    chosen = None
                    for r in rooms_sorted:
                        if r.capacity >= need and r.number not in used_rooms_this_basket:
                            chosen = r.number
                            used_rooms_this_basket.add(r.number)
                            break
                    if not chosen:
                        for r in rooms_sorted:
                            if r.capacity >= need:
                                chosen = r.number
                                break
                    if not chosen:
                        chosen = "TBA"
                    ws.cell(legend_row, column=1).value = basket
                    ws.cell(legend_row, column=2).value = c.code
                    ws.cell(legend_row, column=3).value = ", ".join(c.instructors) if c.instructors else "TBA"
                    ws.cell(legend_row, column=4).value = chosen
                    legend_row += 1

            # Adjust column widths
            for c in range(max_slots + 1):
                col_letter = chr(ord("A") + c)
                ws.column_dimensions[col_letter].width = 22

        # Save workbook per department
        filename = f"{dept}_{term_label}.xlsx"
        filepath = OUTPUT_DIR / filename
        wb.save(filepath)
        print(f"Generated timetable workbook: {filepath}")
# -----------------------------------------
# PART 3/4 — Remaining Helpers
# -----------------------------------------

def determine_basket_for_course(c: Course) -> str:
    """
    Returns basket name based on semester & credits.
    This matches the logic used earlier in scheduler.
    """
    sem = c.semester
    cr = c.credits

    # For sem 1,3,5 normalize to Open Elective naming as requested
    if sem == 1:
        return "Open Elective-1"
    if sem == 3:
        return "Open Elective-3"
    if sem == 5:
        return "Open Elective-5"
    if sem == 7:
        bucket = (abs(hash(c.code)) % 4) + 1
        return f"elective basket 7.{bucket}"
    return f"elective basket {sem}.1"


def is_room_free(room_no: str, day: int, start: int, end: int, room_occupancy) -> bool:
    """
    Checks if room is free for the given interval based on existing occupancy list.
    """
    intervals = room_occupancy.get(room_no, [])
    for d, s, e in intervals:
        if d != day:
            continue
        if not (end <= s or e <= start):
            return False
    return True


def is_room_free_for_assigned(room_no: str, day: int, start: int, end: int, assigned) -> bool:
    """
    Checks whether room is free with respect to ALREADY ASSIGNED rooms in elective legend.
    """
    intervals = assigned.get(room_no, [])
    for d, s, e in intervals:
        if d != day:
            continue
        if not (end <= s or e <= start):
            return False
    return True


def mark_room_assigned(room_no: str, day: int, start: int, end: int, assigned):
    """
    Marks a room as assigned for legend slots.
    """
    assigned[room_no].append((day, start, end))
# -----------------------------------------
# PART 4/4 — Column Width Adjustment + End
# -----------------------------------------

def auto_adjust_column_width(ws, max_slots: int):
    """
    Makes columns wide enough to read comfortably.
    """
    total_cols = max_slots + 1  # +1 for Day column
    for col_index in range(1, total_cols + 1):
        col_letter = chr(ord('A') + col_index - 1)
        ws.column_dimensions[col_letter].width = 23


# -----------------------------------------
# END OF FILE
# -----------------------------------------
