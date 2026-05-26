import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import RoleChecker
from app.models.models import Alarm, UserRole
from app.schemas.schemas import AlarmRead

router = APIRouter()

read_access = Depends(RoleChecker([UserRole.SUPER_ADMIN, UserRole.NOC_ENGINEER, UserRole.READ_ONLY, UserRole.CLIENT_VIEWER]))
write_access = Depends(RoleChecker([UserRole.SUPER_ADMIN, UserRole.NOC_ENGINEER]))

@router.get("/", response_model=List[AlarmRead], dependencies=[read_access])
async def list_alarms(
    active_only: bool = Query(True),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve active or historic system alarms (fiber cuts, LOS, high CPU, offline ONUs)."""
    query = select(Alarm).options(
        selectinload(Alarm.olt),
        selectinload(Alarm.onu)
    )
    
    if active_only:
        query = query.where(Alarm.is_active == True)
        
    query = query.order_by(Alarm.raised_at.desc()).limit(limit)
    
    result = await db.execute(query)
    alarms = result.scalars().all()
    
    # Format return list
    return [
        AlarmRead(
            **alarm.dict(),
            olt_name=alarm.olt.name if alarm.olt else None,
            onu_serial=alarm.onu.serial_number if alarm.onu else None
        ) for alarm in alarms
    ]

@router.post("/{alarm_id}/clear", response_model=AlarmRead, dependencies=[write_access])
async def clear_alarm(alarm_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Acknowledge and clear an active alarm manually."""
    alarm = await db.get(Alarm, alarm_id)
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
        
    if not alarm.is_active:
        raise HTTPException(status_code=400, detail="Alarm is already cleared")
        
    alarm.is_active = False
    alarm.cleared_at = datetime.utcnow()
    
    db.add(alarm)
    await db.commit()
    await db.refresh(alarm)
    
    return alarm
