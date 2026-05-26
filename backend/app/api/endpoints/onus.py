import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import select, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import encryptor
from app.api.deps import get_current_user, RoleChecker
from app.models.models import OLT, PONPort, ONU, AuditLog, User, UserRole, OnuStatus
from app.schemas.schemas import ONURead, ONUUpdate, ONUOperation, BulkONUOperation
from app.services.drivers.factory import OLTDriverFactory

router = APIRouter()

read_access = Depends(RoleChecker([UserRole.SUPER_ADMIN, UserRole.NOC_ENGINEER, UserRole.READ_ONLY, UserRole.CLIENT_VIEWER]))
write_access = Depends(RoleChecker([UserRole.SUPER_ADMIN, UserRole.NOC_ENGINEER]))

@router.get("/", response_model=List[ONURead], dependencies=[read_access])
async def list_onus(
    olt_id: Optional[uuid.UUID] = None,
    pon_port_id: Optional[uuid.UUID] = None,
    status: Optional[OnuStatus] = None,
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List and search ONUs with search term matches on serial, MAC, customer_id, username, or VLAN."""
    query = select(ONU).options(
        selectinload(ONU.olt),
        selectinload(ONU.pon_port)
    )
    
    filters = []
    if olt_id:
        filters.append(ONU.olt_id == olt_id)
    if pon_port_id:
        filters.append(ONU.pon_port_id == pon_port_id)
    if status:
        filters.append(ONU.status == status)
        
    if q:
        # Search across multiple indexes
        q_term = f"%{q}%"
        try:
            vlan_val = int(q)
            vlan_filter = (ONU.vlan == vlan_val)
        except ValueError:
            vlan_filter = (ONU.vlan == -1)
            
        filters.append(or_(
            ONU.serial_number.ilike(q_term),
            ONU.mac_address.ilike(q_term),
            ONU.customer_id.ilike(q_term),
            ONU.username.ilike(q_term),
            vlan_filter
        ))
        
    if filters:
        query = query.where(and_(*filters))
        
    result = await db.execute(query)
    db_onus = result.scalars().all()
    
    # Format return list
    return [
        ONURead(
            **onu.dict(),
            olt_name=onu.olt.name,
            pon_port_number=onu.pon_port.port_number
        ) for onu in db_onus
    ]

@router.post("/{onu_id}/action", dependencies=[write_access])
async def execute_onu_action(
    onu_id: uuid.UUID,
    op: ONUOperation,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger remote CLI operations on OLT for a specific ONU (reboot, disable, enable, change_vlan)."""
    # Preload OLT and PON Port
    result = await db.execute(
        select(ONU).where(ONU.id == onu_id).options(
            selectinload(ONU.olt),
            selectinload(ONU.pon_port)
        )
    )
    onu = result.scalars().first()
    if not onu:
        raise HTTPException(status_code=404, detail="ONU not found")
        
    olt = onu.olt
    
    # Decrypt OLT access credentials
    community = encryptor.decrypt(olt.snmp_community) if olt.snmp_community else "public"
    ssh_pass = encryptor.decrypt(olt.ssh_password) if olt.ssh_password else None
    
    driver = OLTDriverFactory.get_driver(
        vendor=olt.vendor,
        ip_address=olt.ip_address,
        snmp_community=community,
        snmp_port=olt.snmp_port,
        snmp_version=olt.snmp_version,
        ssh_username=olt.ssh_username,
        ssh_password=ssh_pass,
        ssh_port=olt.ssh_port
    )
    
    success = False
    action_performed = op.action.upper()
    details = {"onu_id": str(onu.id), "serial": onu.serial_number, "port": onu.pon_port.port_number}
    
    try:
        if op.action == "reboot":
            success = await driver.reboot_onu(onu.pon_port.port_number, onu.onu_index)
        elif op.action == "disable":
            success = await driver.set_onu_admin_status(onu.pon_port.port_number, onu.onu_index, enable=False)
            if success:
                onu.status = OnuStatus.OFFLINE
                db.add(onu)
        elif op.action == "enable":
            success = await driver.set_onu_admin_status(onu.pon_port.port_number, onu.onu_index, enable=True)
            if success:
                onu.status = OnuStatus.ONLINE
                db.add(onu)
        elif op.action == "change_vlan":
            if not op.vlan:
                raise HTTPException(status_code=400, detail="VLAN ID is required for change_vlan action")
            success = await driver.change_onu_vlan(onu.pon_port.port_number, onu.onu_index, op.vlan)
            if success:
                onu.vlan = op.vlan
                db.add(onu)
            details["vlan"] = op.vlan
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported action: {op.action}")
            
        if not success:
            raise HTTPException(status_code=502, detail="OLT driver failed to execute action. Verify connection status.")
            
        # Log audit entry
        audit = AuditLog(
            user_id=current_user.id,
            action=f"ONU_{action_performed}",
            details=details
        )
        db.add(audit)
        await db.commit()
        
        return {"success": True, "message": f"Successfully executed {op.action} operation."}
        
    except NotImplementedError as ne:
        raise HTTPException(status_code=501, detail=str(ne))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing ONU action: {str(e)}")


@router.post("/bulk-action", dependencies=[write_access])
async def execute_bulk_onu_action(
    bulk_op: BulkONUOperation,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Executes reboot or status disable/enable in bulk across multiple OLTs/ONUs."""
    successful_onus = []
    failed_onus = []
    
    for onu_id in bulk_op.onu_ids:
        res = await db.execute(
            select(ONU).where(ONU.id == onu_id).options(
                selectinload(ONU.olt),
                selectinload(ONU.pon_port)
            )
        )
        onu = res.scalars().first()
        if not onu:
            failed_onus.append(str(onu_id))
            continue
            
        olt = onu.olt
        community = encryptor.decrypt(olt.snmp_community) if olt.snmp_community else "public"
        ssh_pass = encryptor.decrypt(olt.ssh_password) if olt.ssh_password else None
        
        driver = OLTDriverFactory.get_driver(
            vendor=olt.vendor,
            ip_address=olt.ip_address,
            snmp_community=community,
            ssh_username=olt.ssh_username,
            ssh_password=ssh_pass
        )
        
        try:
            success = False
            if bulk_op.action == "reboot":
                success = await driver.reboot_onu(onu.pon_port.port_number, onu.onu_index)
            elif bulk_op.action == "disable":
                success = await driver.set_onu_admin_status(onu.pon_port.port_number, onu.onu_index, enable=False)
                if success:
                    onu.status = OnuStatus.OFFLINE
                    db.add(onu)
            elif bulk_op.action == "enable":
                success = await driver.set_onu_admin_status(onu.pon_port.port_number, onu.onu_index, enable=True)
                if success:
                    onu.status = OnuStatus.ONLINE
                    db.add(onu)
            
            if success:
                successful_onus.append(onu.serial_number)
                audit = AuditLog(
                    user_id=current_user.id,
                    action=f"BULK_ONU_{bulk_op.action.upper()}",
                    details={"onu_id": str(onu.id), "serial": onu.serial_number}
                )
                db.add(audit)
            else:
                failed_onus.append(onu.serial_number)
        except Exception:
            failed_onus.append(onu.serial_number)
            
    await db.commit()
    return {
        "success_count": len(successful_onus),
        "failed_count": len(failed_onus),
        "successful_serials": successful_onus,
        "failed_serials": failed_onus
    }
