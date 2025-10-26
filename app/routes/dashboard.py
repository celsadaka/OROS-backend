from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, date, time, timedelta

from ..dependencies import get_db
from ..models.surgery import surgeries, SurgeryStatus
from ..models.operating_room import operating_rooms
from ..models.note import notes

router = APIRouter()

class ORUtilizationItem(BaseModel):
    room_id: int
    room_number: str
    minutes_busy: int
    minutes_window: int
    utilization_pct: float  

class ORUtilizationResp(BaseModel):
    date: date
    window_start: str
    window_end: str
    per_room: list[ORUtilizationItem]
    top_room_id: int | None
    top_room_number: str | None
    top_utilization_pct: float | None

class NotesTodayResp(BaseModel):
    date: date
    count_today: int
    count_yesterday: int
    delta_vs_yesterday: int  

class AvgWaitResp(BaseModel):
    date: date
    avg_wait_minutes_today: float | None
    avg_wait_minutes_yesterday: float | None
    delta_minutes: float | None  

class PatientsCountResp(BaseModel):
    date: date
    distinct_patients_today: int

class DashboardMetrics(BaseModel):
    or_utilization: ORUtilizationResp
    notes_today: NotesTodayResp
    avg_wait_time: AvgWaitResp
    patients_count: PatientsCountResp


def _clip_overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> int:
    """Return overlap in minutes between [a_start,a_end] and [b_start,b_end]."""
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    if end <= start:
        return 0
    return int((end - start).total_seconds() // 60)


def _day_window(d: date, day_start: time, day_end: time) -> tuple[datetime, datetime]:
    return datetime.combine(d, day_start), datetime.combine(d, day_end)


@router.get("/or-utilization", response_model=ORUtilizationResp)
def or_utilization(
    db: Session = Depends(get_db),
    on: date = Query(default_factory=lambda: date.today()),
    day_start: str = Query("07:00"),  
    day_end: str   = Query("19:00"),
):
    t_start = datetime.strptime(day_start, "%H:%M").time()
    t_end = datetime.strptime(day_end, "%H:%M").time()
    win_start, win_end = _day_window(on, t_start, t_end)
    minutes_window = int((win_end - win_start).total_seconds() // 60)

    rooms = db.query(operating_rooms).all()
    items: list[ORUtilizationItem] = []

    qs = (
        db.query(surgeries)
        .filter(surgeries.status != SurgeryStatus.cancelled)
        .filter(
            (surgeries.scheduled_date == on) |
            (surgeries.actual_start_time >= win_start) & (surgeries.actual_start_time <= win_end)
        )
        .all()
    )

    by_room: dict[int, int] = {r.id: 0 for r in rooms}
    for s in qs:
        if s.actual_start_time and s.actual_end_time:
            a_start, a_end = s.actual_start_time, s.actual_end_time
        else:
            if not s.scheduled_time or not s.duration_minutes:
                continue
            a_start = datetime.combine(s.scheduled_date, s.scheduled_time)
            a_end = a_start + timedelta(minutes=int(s.duration_minutes))
        overlap = _clip_overlap(a_start, a_end, win_start, win_end)
        if overlap and s.operating_room_id in by_room:
            by_room[s.operating_room_id] += overlap

    for r in rooms:
        busy = by_room.get(r.id, 0)
        pct = round(100.0 * busy / minutes_window, 2) if minutes_window else 0.0
        items.append(ORUtilizationItem(
            room_id=r.id, room_number=r.room_number,
            minutes_busy=busy, minutes_window=minutes_window,
            utilization_pct=pct
        ))

    if items:
        top = max(items, key=lambda x: x.utilization_pct)
        top_id, top_num, top_pct = top.room_id, top.room_number, top.utilization_pct
    else:
        top_id = top_num = None
        top_pct = None

    return ORUtilizationResp(
        date=on,
        window_start=day_start,
        window_end=day_end,
        per_room=items,
        top_room_id=top_id,
        top_room_number=top_num,
        top_utilization_pct=top_pct,
    )


@router.get("/notes-today", response_model=NotesTodayResp)
def notes_today(db: Session = Depends(get_db), on: date = Query(default_factory=lambda: date.today())):
    start = datetime.combine(on, time.min)
    end = datetime.combine(on, time.max)
    y_on = on - timedelta(days=1)
    y_start = datetime.combine(y_on, time.min)
    y_end = datetime.combine(y_on, time.max)

    today = db.query(notes).filter(notes.created_at >= start, notes.created_at <= end).count()
    yday = db.query(notes).filter(notes.created_at >= y_start, notes.created_at <= y_end).count()

    return NotesTodayResp(
        date=on, count_today=today, count_yesterday=yday, delta_vs_yesterday=today - yday
    )


@router.get("/avg-wait-time", response_model=AvgWaitResp)
def avg_wait_time(db: Session = Depends(get_db), on: date = Query(default_factory=lambda: date.today())):
    start = datetime.combine(on, time.min)
    end = datetime.combine(on, time.max)
    y_on = on - timedelta(days=1)
    y_start = datetime.combine(y_on, time.min)
    y_end = datetime.combine(y_on, time.max)

    def _avg_between(a: datetime, b: datetime):
        rows = (
            db.query(surgeries)
            .filter(surgeries.status != SurgeryStatus.cancelled)
            .filter(surgeries.actual_start_time >= a, surgeries.actual_start_time <= b)
            .all()
        )
        waits = []
        for s in rows:
            if s.scheduled_time and s.scheduled_date and s.actual_start_time:
                sched_dt = datetime.combine(s.scheduled_date, s.scheduled_time)
                diff = (s.actual_start_time - sched_dt).total_seconds() / 60.0
                waits.append(max(0.0, diff))
        if not waits:
            return None
        return round(sum(waits) / len(waits), 2)

    t_avg = _avg_between(start, end)
    y_avg = _avg_between(y_start, y_end)
    delta = None if (t_avg is None or y_avg is None) else round(t_avg - y_avg, 2)

    return AvgWaitResp(date=on, avg_wait_minutes_today=t_avg, avg_wait_minutes_yesterday=y_avg, delta_minutes=delta)


@router.get("/patients-count", response_model=PatientsCountResp)
def patients_count(db: Session = Depends(get_db), on: date = Query(default_factory=lambda: date.today())):

    start = datetime.combine(on, time.min)
    end = datetime.combine(on, time.max)
    rows = (
        db.query(surgeries.patient_id)
        .filter(surgeries.status != SurgeryStatus.cancelled)
        .filter(
            (surgeries.scheduled_date == on) |
            ((surgeries.actual_start_time >= start) & (surgeries.actual_start_time <= end))
        )
        .distinct()
        .all()
    )
    return PatientsCountResp(date=on, distinct_patients_today=len(rows))


@router.get("/metrics", response_model=DashboardMetrics)
def dashboard_metrics(
    db: Session = Depends(get_db),
    on: date = Query(default_factory=lambda: date.today()),
    day_start: str = Query("07:00"),
    day_end: str   = Query("19:00"),
):
    util = or_utilization(db=db, on=on, day_start=day_start, day_end=day_end)
    notes_resp = notes_today(db=db, on=on)
    wait_resp = avg_wait_time(db=db, on=on)
    patients_resp = patients_count(db=db, on=on)

    return DashboardMetrics(
        or_utilization=util,
        notes_today=notes_resp,
        avg_wait_time=wait_resp,
        patients_count=patients_resp,
    )
