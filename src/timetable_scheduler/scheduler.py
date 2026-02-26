# src/timetable_scheduler/scheduler.py
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict
from math import ceil
from datetime import time as _time

from .models import Course, Room, MinorProgram, ScheduledClass, ScheduleResult
from .config import (
    DAYS,
    WORK_START,
    WORK_END,
    LUNCH_START,
    LUNCH_END,
    MINOR_WINDOWS,
    REGULAR_WINDOW,
    TUTORIAL_DURATION,
    LECTURE_DURATION,
    LAB_DURATION as CONFIG_LAB_DURATION,
    MINOR_DURATION,
    GAP_MINUTES,
    TIME_GRANULARITY,
    STUDENTS_PER_DEPARTMENT,
    get_batch_ids,
    time_to_minutes,
)
from .room_allocator import filter_rooms_for_session

# Use configured lab duration from config (minutes)
# Prefer the value from config so changing config updates scheduler behavior
LAB_DURATION = CONFIG_LAB_DURATION

# -------------------------
# Utility helpers
# -------------------------
def overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return not (a_end <= b_start or b_end <= a_start)


def is_within(start: int, end: int, w_start: int, w_end: int) -> bool:
    return start >= w_start and end <= w_end


def in_lunch(start: int, end: int) -> bool:
    ls = time_to_minutes(LUNCH_START)
    le = time_to_minutes(LUNCH_END)
    return overlaps(start, end, ls, le)


def in_minor_window(start: int, end: int) -> bool:
    for ws, we in MINOR_WINDOWS:
        if overlaps(start, end, time_to_minutes(ws), time_to_minutes(we)):
            return True
    return False


def in_regular_window(start: int, end: int) -> bool:
    ws = time_to_minutes(REGULAR_WINDOW[0])
    we = time_to_minutes(REGULAR_WINDOW[1])
    return is_within(start, end, ws, we)


def has_required_gap(
    new_start: int,
    new_end: int,
    intervals: List[Tuple[int, int]],
    gap: int = GAP_MINUTES,
) -> bool:
    for s, e in intervals:
        if overlaps(new_start - gap, new_end + gap, s, e):
            return False
    return True


def choose_instructor_for_batch(course: Course, batch_idx: int) -> str:
    if not course.instructors:
        return "TBA"
    return course.instructors[batch_idx % len(course.instructors)]


def compute_sessions_for_course(course: Course) -> Dict[str, int]:
    return {
        "lecture": course.l,
        "tutorial": course.t,
        "lab": course.p,
    }


def assign_half_categories(courses: List[Course]) -> None:
    """
    For each (department, semester) group, divide half-semester courses into
    two approximately equal categories: 'Cat-1' and 'Cat-2'. Assignment is
    deterministic (sorted by course code) and alternates to balance count.
    """
    from collections import defaultdict

    groups: Dict[Tuple[str, int], List[Course]] = defaultdict(list)
    for c in courses:
        if c.is_half_semester:
            groups[(c.department, c.semester)].append(c)

    for key, clist in groups.items():
        clist_sorted = sorted(clist, key=lambda x: x.code)
        for i, course in enumerate(clist_sorted):
            course.half_category = "Cat-1" if i % 2 == 0 else "Cat-2"


# -------------------------
# Elective helpers
# -------------------------
def group_electives_by_semester_and_basket(courses: List[Course]) -> Dict[int, Dict[str, List[Course]]]:
    sem_baskets: Dict[int, Dict[str, List[Course]]] = defaultdict(lambda: defaultdict(list))

    for c in courses:
        if not c.is_elective:
            continue
        sem = c.semester
        cr = c.credits
        if sem == 1:
            if cr == 1:
                sem_baskets[1]["elective basket 1.1"].append(c)
            else:
                sem_baskets[1]["elective basket 1.2"].append(c)
        elif sem == 3:
            if cr == 1:
                sem_baskets[3]["elective basket 3.1"].append(c)
            else:
                sem_baskets[3]["elective basket 3.2"].append(c)
        elif sem == 5:
            sem_baskets[5]["elective basket 5.1"].append(c)
        elif sem == 7:
            sem_baskets[7]["__unsorted__"].append(c)
        else:
            sem_baskets[sem][f"elective basket {sem}.1"].append(c)

    if 7 in sem_baskets and "__unsorted__" in sem_baskets[7]:
        uns = sem_baskets[7].pop("__unsorted__")
        for i, c in enumerate(uns):
            bucket = f"elective basket 7.{(i % 4) + 1}"
            sem_baskets[7][bucket].append(c)

    # Combine baskets into 'Open Elective' groups per requirement
    # Semester 1: combine 1.1 & 1.2 -> Open Elective-1
    if 1 in sem_baskets:
        combined = []
        for k in list(sem_baskets[1].keys()):
            combined.extend(sem_baskets[1].pop(k))
        if combined:
            sem_baskets[1]["Open Elective-1"] = combined

    # Semester 3: combine 3.1 & 3.2 -> Open Elective-3
    if 3 in sem_baskets:
        combined = []
        for k in list(sem_baskets[3].keys()):
            combined.extend(sem_baskets[3].pop(k))
        if combined:
            sem_baskets[3]["Open Elective-3"] = combined

    # Semester 5: normalize to Open Elective-5
    if 5 in sem_baskets:
        combined = []
        for k in list(sem_baskets[5].keys()):
            combined.extend(sem_baskets[5].pop(k))
        if combined:
            sem_baskets[5]["Open Elective-5"] = combined

    return sem_baskets


def assign_elective_courses_to_terms(sem_baskets: Dict[int, Dict[str, List[Course]]]) -> Dict[int, Dict[str, Dict[str, List[Course]]]]:
    assignments: Dict[int, Dict[str, Dict[str, List[Course]]]] = defaultdict(lambda: defaultdict(lambda: {"PRE": [], "POST": [], "BOTH": []}))

    for sem, baskets in sem_baskets.items():
        for basket_label, courses in baskets.items():
            if (sem in (1, 3)) and (".1" in basket_label):
                for i, c in enumerate(sorted(courses, key=lambda x: x.code)):
                    if i % 2 == 0:
                        assignments[sem][basket_label]["PRE"].append(c)
                    else:
                        assignments[sem][basket_label]["POST"].append(c)
            elif (sem in (1, 3)) and (".2" in basket_label):
                for c in sorted(courses, key=lambda x: x.code):
                    if c.credits > 2:
                        assignments[sem][basket_label]["BOTH"].append(c)
                    elif c.credits == 2:
                        if (len(assignments[sem][basket_label]["PRE"]) <= len(assignments[sem][basket_label]["POST"])):
                            assignments[sem][basket_label]["PRE"].append(c)
                        else:
                            assignments[sem][basket_label]["POST"].append(c)
                    else:
                        assignments[sem][basket_label]["PRE"].append(c)
            elif sem == 5:
                assignments[sem][basket_label]["BOTH"].extend(sorted(courses, key=lambda x: x.code))
            elif sem == 7:
                assignments[sem][basket_label]["BOTH"].extend(sorted(courses, key=lambda x: x.code))
            else:
                assignments[sem][basket_label]["BOTH"].extend(sorted(courses, key=lambda x: x.code))

    return assignments


# -------------------------
# Elective scheduling
# -------------------------
def schedule_elective_baskets_for_term(
    result: ScheduleResult,
    state: dict,
    assignments: Dict[int, Dict[str, Dict[str, List[Course]]]],
    term: str,
):
    batch_intervals = state["batch_intervals"]

    lec_slot_start = time_to_minutes(_time(16, 0))
    lec_slot_end = lec_slot_start + 90
    tut_slot_start = time_to_minutes(_time(16, 30))
    tut_slot_end = tut_slot_start + 60

    sem7_window_start = time_to_minutes(_time(9, 0))
    sem7_window_end = time_to_minutes(_time(18, 30))

    def place_basket_label(batch_id: str, day_index: int, start: int, end: int, label: str):
        sc = ScheduledClass(
            day_index=day_index,
            start_minute=start,
            duration=(end - start),
            batch_id=batch_id,
            term=term,
            course_code=label,
            course_name=None,
            instructor=None,
            room_number=None,
            is_minor=False,
            minor_name=None,
            is_lab=False,
            is_tutorial=False,
            is_lecture=True,
        )
        result.scheduled_classes.append(sc)
        batch_intervals[(day_index, batch_id)].append((start, end))

    def slot_free_for_all(batches: List[str], day_index: int, start: int, end: int) -> bool:
        for b in batches:
            if not has_required_gap(start, end, batch_intervals[(day_index, b)]):
                return False
        return True

    sem7_batches_all: List[str] = []
    for dept in STUDENTS_PER_DEPARTMENT.keys():
        sem7_batches_all.extend(get_batch_ids(dept, 7))
    sem7_batches_all = sorted(set(sem7_batches_all))

    for sem, baskets in assignments.items():
        for basket_label, mapping in baskets.items():
            has_term_courses = False
            if term == "PRE" and mapping.get("PRE"):
                has_term_courses = True
            if term == "POST" and mapping.get("POST"):
                has_term_courses = True
            if mapping.get("BOTH"):
                has_term_courses = True
            if not has_term_courses:
                continue

            if sem == 7:
                target_batches = sem7_batches_all
            else:
                target_batches = []
                for dept in STUDENTS_PER_DEPARTMENT.keys():
                    target_batches.extend(get_batch_ids(dept, sem))
            target_batches = sorted(set(target_batches))
            if not target_batches:
                continue

            lec_count = 2
            tut_needed = False
            if sem in (1, 3, 5):
                lec_count = 2
            if sem == 7:
                lec_count = 3
                tut_needed = True
            if ("1.2" in basket_label) or ("3.2" in basket_label) or ("5.1" in basket_label) or basket_label.startswith("elective basket 7"):
                tut_needed = True

            if sem != 7:
                lecture_slots = [(0, lec_slot_start, lec_slot_end), (2, lec_slot_start, lec_slot_end)]
                lecture_slots = lecture_slots[:lec_count]
                for batch_id in target_batches:
                    for (d, s, e) in lecture_slots:
                        if has_required_gap(s, e, batch_intervals[(d, batch_id)]):
                            place_basket_label(batch_id, d, s, e, basket_label)
                        else:
                            result.warnings.append(
                                f"Could not place {basket_label} lecture (term {term}) for batch {batch_id} at day {d} {s}-{e} (clash)."
                            )
                    if tut_needed:
                        d, s, e = (4, tut_slot_start, tut_slot_end)
                        if has_required_gap(s, e, batch_intervals[(d, batch_id)]):
                            place_basket_label(batch_id, d, s, e, f"{basket_label}-TUT")
                        else:
                            result.warnings.append(
                                f"Could not place {basket_label}-TUT (term {term}) for batch {batch_id} at day {d} {s}-{e} (clash)."
                            )
                continue

            # sem 7 dynamic placement
            if sem == 7:
                found_lecture_slots: List[Tuple[int, int, int]] = []
                for day_index in range(0, 5):
                    if len(found_lecture_slots) >= lec_count:
                        break
                    start = sem7_window_start
                    last_start = sem7_window_end - 90
                    while start <= last_start and len(found_lecture_slots) < lec_count:
                        end = start + 90
                        if in_lunch(start, end):
                            start += TIME_GRANULARITY
                            continue
                        if slot_free_for_all(target_batches, day_index, start, end):
                            conflict_with_selected = False
                            for (sd, ss, se) in found_lecture_slots:
                                if sd == day_index and overlaps(start, end, ss, se):
                                    conflict_with_selected = True
                                    break
                            if not conflict_with_selected:
                                found_lecture_slots.append((day_index, start, end))
                                start = end + TIME_GRANULARITY
                                continue
                        start += TIME_GRANULARITY

                if len(found_lecture_slots) < lec_count:
                    result.warnings.append(
                        f"Could not find {lec_count} global lecture slots for {basket_label} (sem7 term {term}). Found {len(found_lecture_slots)}."
                    )
                else:
                    for (d, s, e) in found_lecture_slots:
                        for batch_id in target_batches:
                            place_basket_label(batch_id, d, s, e, basket_label)

                # tutorial
                found_tut_slot = None
                tut_last_start = sem7_window_end - 60
                for day_index in range(0, 5):
                    start = sem7_window_start
                    while start <= tut_last_start:
                        end = start + 60
                        if in_lunch(start, end):
                            start += TIME_GRANULARITY
                            continue
                        if slot_free_for_all(target_batches, day_index, start, end):
                            found_tut_slot = (day_index, start, end)
                            break
                        start += TIME_GRANULARITY
                    if found_tut_slot:
                        break

                if not found_tut_slot:
                    result.warnings.append(
                        f"Could not find tutorial slot for {basket_label} (sem7 term {term})."
                    )
                else:
                    d, s, e = found_tut_slot
                    for batch_id in target_batches:
                        place_basket_label(batch_id, d, s, e, f"{basket_label}-TUT")


# -------------------------
# Main scheduling flow
# -------------------------
def schedule_all(
    courses: List[Course],
    rooms: List[Room],
    minors: List[MinorProgram],
) -> Tuple[ScheduleResult, ScheduleResult]:
    pre = ScheduleResult()
    post = ScheduleResult()

    pre_state = build_empty_state()
    post_state = build_empty_state()

    # Assign half-semester categories (Cat-1 / Cat-2) before creating baskets
    assign_half_categories(courses)

    sem_baskets = group_electives_by_semester_and_basket(courses)
    assignments = assign_elective_courses_to_terms(sem_baskets)

    non_elective_courses = [c for c in courses if not c.is_elective]

    # PRE
    schedule_elective_baskets_for_term(pre, pre_state, assignments, term="PRE")
    _schedule_core_courses_for_term(non_elective_courses, rooms, pre, pre_state, term="PRE")
    schedule_minors_simple(pre, pre_state, term="PRE")

    # POST
    schedule_elective_baskets_for_term(post, post_state, assignments, term="POST")
    _schedule_core_courses_for_term(non_elective_courses, rooms, post, post_state, term="POST")
    schedule_minors_simple(post, post_state, term="POST")

    return pre, post


# -------------------------
# Core scheduling per-term helpers
# -------------------------
def _schedule_core_courses_for_term(courses: List[Course], rooms: List[Room], result: ScheduleResult, state: dict, term: str):
    dept_sem_courses: Dict[Tuple[str, int], List[Course]] = defaultdict(list)
    for c in courses:
        dept_sem_courses[(c.department, c.semester)].append(c)

    for (dept, sem), course_list in dept_sem_courses.items():
        batch_ids = get_batch_ids(dept, sem)
        for course in course_list:
            multiple_batches = len(batch_ids) > 1
            only_one_instructor = len(course.instructors) == 1
            sessions = compute_sessions_for_course(course)

            for idx, batch_id in enumerate(batch_ids):
                # Default: both terms
                pre_term = True
                post_term = True

                # If this is a half-semester course, use assigned Cat-1/Cat-2
                if course.is_half_semester:
                    if course.half_category == "Cat-1":
                        pre_term = True
                        post_term = False
                    elif course.half_category == "Cat-2":
                        pre_term = False
                        post_term = True
                    else:
                        # fallback: keep both
                        pre_term = True
                        post_term = True
                else:
                    # preserve prior heuristic for very short/elective courses
                    half_low = course.is_elective and course.credits <= 2
                    if half_low and multiple_batches and only_one_instructor:
                        pre_term = idx == 0
                        post_term = idx != 0

                if term == "PRE" and not pre_term:
                    continue
                if term == "POST" and not post_term:
                    continue

                instructor = choose_instructor_for_batch(course, idx)
                schedule_course_for_batch(
                    result=result,
                    state=state,
                    course=course,
                    batch_id=batch_id,
                    instructor=instructor,
                    rooms=rooms,
                    sessions=sessions,
                    term=term,
                    elective=False,
                    all_batch_ids=batch_ids,
                )


# -------------------------
# Minor scheduling: fixed windows morning + evening (07:30-09:00, 18:30-20:00)
# -------------------------
def schedule_minors_simple(result: ScheduleResult, state: dict, term: str):
    batch_intervals = state["batch_intervals"]

    minor_windows_fixed = [
        (_time(7, 30), _time(9, 0)),
        (_time(18, 30), _time(20, 0)),
    ]

    batches_in_term: Set[str] = {sc.batch_id for sc in result.scheduled_classes if sc.term == term}

    for batch_id in batches_in_term:
        parts = batch_id.split("_")
        if len(parts) < 2 or not parts[1].upper().startswith("SEM"):
            continue
        try:
            sem = int(parts[1][3:])
        except ValueError:
            continue
        if sem not in (3, 5):
            continue

        for day_index, _ in enumerate(DAYS):
            for ws, we in minor_windows_fixed:
                s = time_to_minutes(ws)
                e = time_to_minutes(we)
                intervals = batch_intervals[(day_index, batch_id)]
                clash = any(overlaps(c_s, c_e, s, e) for (c_s, c_e) in intervals)
                if clash:
                    continue

                sc = ScheduledClass(
                    day_index=day_index,
                    start_minute=s,
                    duration=(e - s),
                    batch_id=batch_id,
                    term=term,
                    course_code=None,
                    course_name=None,
                    instructor=None,
                    room_number=None,
                    is_minor=True,
                    minor_name="Minor",
                    is_lab=False,
                    is_tutorial=False,
                    is_lecture=False,
                )
                result.scheduled_classes.append(sc)
                batch_intervals[(day_index, batch_id)].append((s, e))


# -------------------------
# Scheduling per-course sessions (lecture, tutorial, lab)
# -------------------------
def schedule_course_for_batch(
    result: ScheduleResult,
    state: dict,
    course: Course,
    batch_id: str,
    instructor: str,
    rooms: List[Room],
    sessions: Dict[str, int],
    term: str,
    elective: bool,
    all_batch_ids: List[str],
):
    for _ in range(sessions["lecture"]):
        place_session(
            result=result,
            state=state,
            course=course,
            batch_id=batch_id,
            instructor=instructor,
            rooms=rooms,
            term=term,
            session_type="lecture",
            elective=elective,
            all_batch_ids=all_batch_ids,
        )
    for _ in range(sessions["tutorial"]):
        place_session(
            result=result,
            state=state,
            course=course,
            batch_id=batch_id,
            instructor=instructor,
            rooms=rooms,
            term=term,
            session_type="tutorial",
            elective=elective,
            all_batch_ids=all_batch_ids,
        )
    for _ in range(sessions["lab"]):
        # try to schedule this lab as two parallel groups (G1, G2) at same start time
        place_lab_parallel(
            result=result,
            state=state,
            course=course,
            batch_id=batch_id,
            instructor=instructor,
            rooms=rooms,
            term=term,
            elective=elective,
            all_batch_ids=all_batch_ids,
        )


def place_lab_parallel(
    result: ScheduleResult,
    state: dict,
    course: Course,
    batch_id: str,
    instructor: str,
    rooms: List[Room],
    term: str,
    elective: bool,
    all_batch_ids: List[str],
) -> bool:
    """
    Attempt to find a start time and two distinct rooms where both halves of the batch can run in parallel.
    Placement preference per Option 2 (Prefer after-lunch slots).
    """
    batch_intervals = state["batch_intervals"]
    room_intervals = state["room_intervals"]
    instr_intervals = state["instr_intervals"]

    total_students = course.registered_students or STUDENTS_PER_DEPARTMENT.get(course.department, 0)
    group_size = ceil(total_students / 2)

    # candidate rooms for labs (rooms that are allowed for labs and fit group_size)
    candidate_rooms_all = filter_rooms_for_session(
        rooms=rooms, is_lab=True, is_minor=False, required_capacity=group_size
    )
    candidate_rooms_all = sorted(candidate_rooms_all, key=lambda r: r.capacity)
    if len(candidate_rooms_all) < 2:
        result.warnings.append(
            f"Could not place parallel lab for course {course.code} batch {batch_id} term {term}: not enough lab rooms for group size {group_size}."
        )
        result.unscheduled.append(f"{course.code}-{batch_id}-lab-{term}")
        return False

    ls = time_to_minutes(LUNCH_START)
    le = time_to_minutes(LUNCH_END)

    # Preferred days: try lecture days first, then other days
    lect_days = set()
    for sc in result.scheduled_classes:
        if sc.batch_id == batch_id and sc.course_code == course.code and sc.is_lecture and sc.term == term:
            lect_days.add(sc.day_index)
    days_order = list(sorted(lect_days)) + [d for d in range(len(DAYS)) if d not in lect_days] if lect_days else list(range(len(DAYS)))

    # We will attempt times in this preference order (Option 2):
    # 1) after-lunch slots (start >= le)
    # 2) before-lunch slots (end <= ls)
    # 3) partial overlap with lunch (start < le and end > ls) as fallback
    for day_index in days_order:
        # build three lists of candidate starts for that day
        day_start = time_to_minutes(WORK_START)
        day_end = time_to_minutes(WORK_END) - LAB_DURATION

        after_candidates = []
        before_candidates = []
        overlap_candidates = []

        for start in range(day_start, day_end + 1, TIME_GRANULARITY):
            end = start + LAB_DURATION
            if in_minor_window(start, end):
                continue
            # skip fully inside lunch
            if start >= ls and end <= le:
                continue
            # room & simple time feasibility will be checked below

            if start >= le:
                after_candidates.append(start)
            elif end <= ls:
                before_candidates.append(start)
            else:
                # partial overlap
                overlap_candidates.append(start)

        # try in order: after -> before -> overlap
        for candidate_list in (after_candidates, before_candidates, overlap_candidates):
            for start in candidate_list:
                end = start + LAB_DURATION

                # check instructor conflict (none used for labs by design, but keep safe)
                if instructor:
                    if any(overlaps(start, end, s2, e2) for (s2, e2) in instr_intervals[(day_index, instructor)]):
                        continue

                # find two free rooms for this interval
                found_pair = None
                for i in range(len(candidate_rooms_all)):
                    r1 = candidate_rooms_all[i]
                    # room must be free
                    if any(overlaps(start, end, s2, e2) for (s2, e2) in room_intervals[(day_index, r1.number)]):
                        continue
                    for j in range(i + 1, len(candidate_rooms_all)):
                        r2 = candidate_rooms_all[j]
                        if any(overlaps(start, end, s2, e2) for (s2, e2) in room_intervals[(day_index, r2.number)]):
                            continue
                        if r1.number == r2.number:
                            continue
                        found_pair = (r1, r2)
                        break
                    if found_pair:
                        break

                if not found_pair:
                    continue

                # place G1 & G2
                r1, r2 = found_pair
                g1_id = f"{batch_id}-G1"
                g2_id = f"{batch_id}-G2"

                sc1 = ScheduledClass(
                    day_index=day_index,
                    start_minute=start,
                    duration=LAB_DURATION,
                    batch_id=g1_id,
                    term=term,
                    course_code=course.code,
                    course_name=course.name,
                    instructor=None,
                    room_number=r1.number,
                    is_minor=False,
                    minor_name=None,
                    is_lab=True,
                    is_tutorial=False,
                    is_lecture=False,
                )
                sc2 = ScheduledClass(
                    day_index=day_index,
                    start_minute=start,
                    duration=LAB_DURATION,
                    batch_id=g2_id,
                    term=term,
                    course_code=course.code,
                    course_name=course.name,
                    instructor=None,
                    room_number=r2.number,
                    is_minor=False,
                    minor_name=None,
                    is_lab=True,
                    is_tutorial=False,
                    is_lecture=False,
                )

                result.scheduled_classes.append(sc1)
                result.scheduled_classes.append(sc2)

                interval = (start, end)
                state["batch_intervals"][(day_index, g1_id)].append(interval)
                state["batch_intervals"][(day_index, g2_id)].append(interval)
                state["room_intervals"][(day_index, r1.number)].append(interval)
                state["room_intervals"][(day_index, r2.number)].append(interval)
                # do not update instr_intervals because instructor=None for labs

                state["batch_day_load"][(day_index, batch_id)] += LAB_DURATION

                return True

    # failed to place
    result.warnings.append(
        f"Could not place parallel lab (two-room simultaneous) for course {course.code} batch {batch_id} term {term}."
    )
    result.unscheduled.append(f"{course.code}-{batch_id}-lab-{term}")
    return False


def place_session(
    result: ScheduleResult,
    state: dict,
    course: Course,
    batch_id: str,
    instructor: str,
    rooms: List[Room],
    term: str,
    session_type: str,
    elective: bool,
    all_batch_ids: List[str],
    same_day_as_lecture: bool = False,
) -> bool:
    if session_type == "lecture":
        duration = LECTURE_DURATION
        is_lab = False
        is_tutorial = False
        is_lecture = True
    elif session_type == "tutorial":
        duration = TUTORIAL_DURATION
        is_lab = False
        is_tutorial = True
        is_lecture = False
    elif session_type == "lab":
        return place_lab_parallel(
            result=result,
            state=state,
            course=course,
            batch_id=batch_id,
            instructor=instructor,
            rooms=rooms,
            term=term,
            elective=elective,
            all_batch_ids=all_batch_ids,
        )
    else:
        return False

    batch_intervals = state["batch_intervals"]
    room_intervals = state["room_intervals"]
    instr_intervals = state["instr_intervals"]
    batch_day_load = state["batch_day_load"]
    batch_before_lunch = state["batch_before_lunch"]
    batch_after_lunch = state["batch_after_lunch"]

    required_students = course.registered_students or STUDENTS_PER_DEPARTMENT.get(
        course.department, 0
    )

    preferred_days = list(range(len(DAYS)))
    if same_day_as_lecture:
        lect_days = set()
        for sc in result.scheduled_classes:
            if (
                sc.batch_id == batch_id
                and sc.course_code == course.code
                and sc.is_lecture
                and sc.term == term
            ):
                lect_days.add(sc.day_index)
        if lect_days:
            preferred_days = list(sorted(lect_days)) + [d for d in range(len(DAYS)) if d not in lect_days]

    def day_load_key(day: int):
        return batch_day_load[(day, batch_id)]

    preferred_days = sorted(preferred_days, key=day_load_key)

    for day_index in preferred_days:
        day_start = time_to_minutes(WORK_START)
        day_end = time_to_minutes(WORK_END) - duration
        for start in range(day_start, day_end + 1, TIME_GRANULARITY):
            end = start + duration

            if not in_regular_window(start, end):
                continue
            if in_lunch(start, end):
                continue

            ls = time_to_minutes(LUNCH_START)

            if end <= ls:
                side = "before"
            elif start >= ls:
                side = "after"
            else:
                side = "mixed"

            if side == "before":
                before = batch_before_lunch[(day_index, batch_id)]
                after = batch_after_lunch[(day_index, batch_id)]
                if before > after + 1:
                    continue
            elif side == "after":
                before = batch_before_lunch[(day_index, batch_id)]
                after = batch_after_lunch[(day_index, batch_id)]
                if after > before + 1:
                    continue

            batch_key = (day_index, batch_id)
            instr_key = (day_index, instructor)
            if not has_required_gap(start, end, batch_intervals[batch_key]):
                continue
            if not has_required_gap(start, end, instr_intervals[instr_key]):
                continue

            if elective:
                can_place_for_all = True
                for b in all_batch_ids:
                    b_key = (day_index, b)
                    if not has_required_gap(start, end, batch_intervals[b_key]):
                        can_place_for_all = False
                        break
                if not can_place_for_all:
                    continue

            candidate_rooms = filter_rooms_for_session(
                rooms=rooms,
                is_lab=False,
                is_minor=False,
                required_capacity=required_students,
            )
            candidate_rooms = sorted(candidate_rooms, key=lambda r: r.capacity)
            for room in candidate_rooms:
                room_key = (day_index, room.number)
                if not has_required_gap(start, end, room_intervals[room_key]):
                    continue

                sc = ScheduledClass(
                    day_index=day_index,
                    start_minute=start,
                    duration=duration,
                    batch_id=batch_id,
                    term=term,
                    course_code=course.code,
                    course_name=course.name,
                    instructor=instructor,
                    room_number=room.number,
                    is_minor=False,
                    minor_name=None,
                    is_lab=False,
                    is_tutorial=is_tutorial,
                    is_lecture=is_lecture,
                )
                result.scheduled_classes.append(sc)

                interval = (start, end)
                batch_intervals[batch_key].append(interval)
                instr_intervals[instr_key].append(interval)
                room_intervals[room_key].append(interval)
                batch_day_load[(day_index, batch_id)] += duration

                if side == "before":
                    batch_before_lunch[(day_index, batch_id)] += 1
                elif side == "after":
                    batch_after_lunch[(day_index, batch_id)] += 1

                return True

    result.warnings.append(
        f"Could not schedule {session_type} for course {course.code} batch {batch_id} term {term}."
    )
    result.unscheduled.append(f"{course.code}-{batch_id}-{session_type}-{term}")
    return False


# -------------------------
# State builder
# -------------------------
def build_empty_state():
    return {
        "batch_intervals": defaultdict(list),
        "room_intervals": defaultdict(list),
        "instr_intervals": defaultdict(list),
        "batch_day_load": defaultdict(int),
        "batch_before_lunch": defaultdict(int),
        "batch_after_lunch": defaultdict(int),
    }
