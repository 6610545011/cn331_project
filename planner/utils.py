from datetime import time
import math
from typing import Dict, Set

from django.core.exceptions import ValidationError

from .models import SectionSchedule

# Slot system constants
SLOT_START = time(8, 0)   # first slot starts at 08:00
SLOT_END = time(20, 0)    # last slot ends at 20:00
SLOT_DURATION_MINUTES = 30
SLOTS_PER_DAY = 24


def _TimeError(msg):
    return ValidationError(msg)


def _time_to_slot_float(t: time) -> float:
    """Return slot index as float where 0.0 corresponds to 08:00.

    Example: 08:00 -> 0.0, 08:30 -> 1.0, 09:15 -> 2.5
    """
    minutes_since_start = (t.hour * 60 + t.minute) - (SLOT_START.hour * 60 + SLOT_START.minute)
    return minutes_since_start / SLOT_DURATION_MINUTES


def _time_to_slot_range(t_start: time, t_end: time) -> Set[int]:
    """Convert a start/end time into a set of occupied slot indices.

    Slots are half-open: a class occupying 09:00-10:00 will occupy slots for
    09:00-09:30 and 09:30-10:00.
    """
    # Validate within overall range
    if t_end <= t_start:
        return set()

    # compute floats
    start_f = _time_to_slot_float(t_start)
    end_f = _time_to_slot_float(t_end)

    # Convert to integer slot indices (start inclusive, end exclusive)
    start_idx = math.floor(start_f)
    end_idx = math.ceil(end_f)

    # clamp to allowed slots
    start_idx = max(0, start_idx)
    end_idx = min(SLOTS_PER_DAY, end_idx)

    return set(range(start_idx, end_idx))


def section_to_slots(section) -> Dict[int, Set[int]]:
    """Return a mapping day_of_week -> set(slot indices) for the given section.

    Expects that `SectionSchedule` rows exist for the section.
    """
    slots_by_day = {d: set() for d in range(7)}
    qs = SectionSchedule.objects.filter(section=section)
    for ss in qs:
        slots = _time_to_slot_range(ss.start_time, ss.end_time)
        if not slots:
            continue
        slots_by_day[ss.day_of_week].update(slots)
    return slots_by_day


def planner_occupied_slots(planner) -> Dict[int, Set[int]]:
    """Return occupied slots mapping for all sections in a user's planner."""
    occupied = {d: set() for d in range(7)}
    for section in planner.sections.all():
        s_slots = section_to_slots(section)
        for d, s in s_slots.items():
            occupied[d].update(s)
    return occupied


def check_conflicts(planner, section_to_add):
    """Check whether adding `section_to_add` would conflict with `planner`.

    Raises `ValidationError` with details when a conflict is found.
    Returns a dict with 'ok': True and optional warnings when no conflict.
    """
    occupied = planner_occupied_slots(planner)
    new_slots = section_to_slots(section_to_add)

    overlaps = []
    for day, slots in new_slots.items():
        if not slots:
            continue
        intersect = occupied.get(day, set()).intersection(slots)
        if intersect:
            overlaps.append({'day': day, 'slots': sorted(list(intersect))})

    if overlaps:
        # Build readable message
        messages = []
        for o in overlaps:
            messages.append(f"Day {o['day']} overlapping slots: {o['slots']}")
        raise ValidationError({'conflict': ' ; '.join(messages)})

    # No time conflicts; compute credit warning
    try:
        current_credits = planner.total_credits()
    except Exception:
        # planner may not have total_credits; compute manually
        current_credits = sum([s.course.credit or 0 for s in planner.sections.select_related('course').all()])

    add_credit = section_to_add.course.credit or 0
    total = current_credits + add_credit

    warning = None
    if total < 9 or total > 22:
        warning = f"Total credits after adding: {total} (recommended 9-22)"

    return {'ok': True, 'warning': warning, 'total_credits': total}
