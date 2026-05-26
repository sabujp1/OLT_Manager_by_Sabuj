from fastapi import APIRouter, Depends
from sqlmodel import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.core.database import get_db
from app.api.deps import RoleChecker
from app.models.models import OLT, PONPort, ONU, Alarm, AlarmType, UserRole, DeviceStatus, OnuStatus, MetricHistory
from app.schemas.schemas import AlarmRead

router = APIRouter()

read_access = Depends(RoleChecker([UserRole.SUPER_ADMIN, UserRole.NOC_ENGINEER, UserRole.READ_ONLY, UserRole.CLIENT_VIEWER]))

@router.get("/stats", response_model=Dict[str, Any], dependencies=[read_access])
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate total counters and state distributions for NOC dashboard widgets."""
    # 1. OLT stats
    olt_total = (await db.execute(select(func.count(OLT.id)))).scalar() or 0
    olt_online = (await db.execute(select(func.count(OLT.id)).where(OLT.status == DeviceStatus.ONLINE))).scalar() or 0
    olt_offline = olt_total - olt_online
    
    # 2. PON Port stats
    pon_total = (await db.execute(select(func.count(PONPort.id)))).scalar() or 0
    
    # 3. ONU stats
    onu_total = (await db.execute(select(func.count(ONU.id)))).scalar() or 0
    onu_online = (await db.execute(select(func.count(ONU.id)).where(ONU.status == OnuStatus.ONLINE))).scalar() or 0
    onu_offline = onu_total - onu_online
    
    # 4. Alarms stats
    active_alarms = (await db.execute(select(func.count(Alarm.id)).where(Alarm.is_active == True))).scalar() or 0
    fiber_cuts = (await db.execute(select(func.count(Alarm.id)).where(and_(Alarm.is_active == True, Alarm.alarm_type == AlarmType.FIBER_CUT)))).scalar() or 0
    dying_gasps = (await db.execute(select(func.count(Alarm.id)).where(and_(Alarm.is_active == True, Alarm.alarm_type == AlarmType.DYING_GASP)))).scalar() or 0
    los_alarms = (await db.execute(select(func.count(Alarm.id)).where(and_(Alarm.is_active == True, Alarm.alarm_type == AlarmType.LOS)))).scalar() or 0
    
    # 5. CPU/RAM Average
    cpu_avg = (await db.execute(select(func.avg(OLT.cpu_usage)))).scalar() or 0.0
    ram_avg = (await db.execute(select(func.avg(OLT.ram_usage)))).scalar() or 0.0
    temp_avg = (await db.execute(select(func.avg(OLT.temperature)))).scalar() or 0.0
    
    # 6. Retrieve 10 most recent active alarms
    alarm_q = await db.execute(
        select(Alarm).where(Alarm.is_active == True)
        .options(selectinload(Alarm.olt), selectinload(Alarm.onu))
        .order_by(Alarm.raised_at.desc()).limit(10)
    )
    recent_alarms = [
        AlarmRead(
            **alarm.dict(),
            olt_name=alarm.olt.name if alarm.olt else None,
            onu_serial=alarm.onu.serial_number if alarm.onu else None
        ) for alarm in alarm_q.scalars().all()
    ]
    
    # 7. Mock traffic chart data for the past 6 hours (in a real app, this would query aggregated MetricHistory)
    traffic_chart = []
    now = datetime.utcnow()
    for i in range(6, 0, -1):
        time_slot = now - timedelta(hours=i)
        # Average simulated values mapping to past hours
        traffic_chart.append({
            "time": time_slot.strftime("%H:%M"),
            "inbound": round(150 + i * 15 + (i % 2) * 10, 1), # Gbps
            "outbound": round(280 + i * 22 - (i % 3) * 5, 1)  # Gbps
        })

    return {
        "olt": {
            "total": olt_total,
            "online": olt_online,
            "offline": olt_offline
        },
        "pon": {
            "total": pon_total
        },
        "onu": {
            "total": onu_total,
            "online": onu_online,
            "offline": onu_offline
        },
        "alarms": {
            "total_active": active_alarms,
            "fiber_cuts": fiber_cuts,
            "dying_gasps": dying_gasps,
            "los": los_alarms
        },
        "telemetry_avg": {
            "cpu": round(float(cpu_avg), 1),
            "ram": round(float(ram_avg), 1),
            "temp": round(float(temp_avg), 1)
        },
        "recent_alarms": recent_alarms,
        "traffic_chart": traffic_chart
    }
