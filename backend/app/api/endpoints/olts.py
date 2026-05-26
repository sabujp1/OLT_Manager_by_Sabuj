import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import encryptor
from app.api.deps import get_current_user, RoleChecker
from app.models.models import OLT, UserRole, DeviceStatus
from app.schemas.schemas import OLTRead, OLTCreate, OLTUpdate, OLTConnectionTest, OLTConnectionTestResult
from app.services.drivers.factory import OLTDriverFactory

router = APIRouter()

# Role checkers
read_access = Depends(RoleChecker([UserRole.SUPER_ADMIN, UserRole.NOC_ENGINEER, UserRole.READ_ONLY, UserRole.CLIENT_VIEWER]))
write_access = Depends(RoleChecker([UserRole.SUPER_ADMIN, UserRole.NOC_ENGINEER]))

@router.get("/", response_model=List[OLTRead], dependencies=[read_access])
async def list_olts(db: AsyncSession = Depends(get_db)):
    """List all configured OLTs in the system."""
    result = await db.execute(select(OLT))
    return result.scalars().all()

@router.get("/{olt_id}", response_model=OLTRead, dependencies=[read_access])
async def get_olt(olt_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve details for a single OLT."""
    olt = await db.get(OLT, olt_id)
    if not olt:
        raise HTTPException(status_code=404, detail="OLT device not found")
    return olt

@router.post("/", response_model=OLTRead, status_code=201, dependencies=[write_access])
async def create_olt(olt_in: OLTCreate, db: AsyncSession = Depends(get_db)):
    """Add a new OLT, encrypting connection secrets at rest."""
    # Ensure IP address is unique
    existing = await db.execute(select(OLT).where(OLT.ip_address == olt_in.ip_address))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="OLT with this IP address already registered")
        
    olt = OLT(**olt_in.dict(exclude={"snmp_community", "ssh_password", "snmp_v3_auth_key", "snmp_v3_priv_key", "api_token"}))
    
    # Encrypt credentials before saving to PostgreSQL
    if olt_in.snmp_community:
        olt.snmp_community = encryptor.encrypt(olt_in.snmp_community)
    if olt_in.ssh_password:
        olt.ssh_password = encryptor.encrypt(olt_in.ssh_password)
    if olt_in.snmp_v3_auth_key:
        olt.snmp_v3_auth_key = encryptor.encrypt(olt_in.snmp_v3_auth_key)
    if olt_in.snmp_v3_priv_key:
        olt.snmp_v3_priv_key = encryptor.encrypt(olt_in.snmp_v3_priv_key)
    if olt_in.api_token:
        olt.api_token = encryptor.encrypt(olt_in.api_token)
        
    db.add(olt)
    await db.commit()
    await db.refresh(olt)
    return olt

@router.put("/{olt_id}", response_model=OLTRead, dependencies=[write_access])
async def update_olt(olt_id: uuid.UUID, olt_in: OLTUpdate, db: AsyncSession = Depends(get_db)):
    """Update OLT details, keeping encrypted credentials safe."""
    olt = await db.get(OLT, olt_id)
    if not olt:
        raise HTTPException(status_code=404, detail="OLT device not found")
        
    update_data = olt_in.dict(exclude_unset=True)
    
    for field, val in update_data.items():
        if field in ["snmp_community", "ssh_password", "snmp_v3_auth_key", "snmp_v3_priv_key", "api_token"]:
            if val:
                setattr(olt, field, encryptor.encrypt(val))
        else:
            setattr(olt, field, val)
            
    db.add(olt)
    await db.commit()
    await db.refresh(olt)
    return olt

@router.delete("/{olt_id}", status_code=204, dependencies=[write_access])
async def delete_olt(olt_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Remove OLT device from the system configuration."""
    olt = await db.get(OLT, olt_id)
    if not olt:
        raise HTTPException(status_code=404, detail="OLT device not found")
    await db.delete(olt)
    await db.commit()
    return None

@router.post("/test-connection", response_model=OLTConnectionTestResult, dependencies=[write_access])
async def test_olt_connection(test_in: OLTConnectionTest):
    """Test SSH/SNMP reachability of an OLT before registering it."""
    try:
        driver = OLTDriverFactory.get_driver(
            vendor=test_in.vendor,
            ip_address=test_in.ip_address,
            snmp_community=test_in.snmp_community or "public",
            ssh_username=test_in.ssh_username,
            ssh_password=test_in.ssh_password,
            ssh_port=test_in.ssh_port
        )
        
        success = await driver.test_connection()
        if success:
            details = {}
            if test_in.connection_method == "SNMP":
                try:
                    sys_met = await driver.get_system_metrics()
                    details = sys_met.dict()
                except Exception:
                    pass
            return OLTConnectionTestResult(
                success=True,
                message="Successfully established connection with the OLT device.",
                details=details
            )
        else:
            return OLTConnectionTestResult(
                success=False,
                message="Failed to connect to the OLT. Verify IP address, ports, and credentials."
            )
    except Exception as e:
        return OLTConnectionTestResult(
            success=False,
            message=f"Connection test error: {str(e)}"
        )
