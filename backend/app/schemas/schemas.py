import uuid
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field

from app.models.models import UserRole, OltVendor, ConnectionMethod, DeviceStatus, OnuStatus, AlarmType, AlarmSeverity

# ----------------- User Schemas -----------------
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.READ_ONLY
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserRead(UserBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Auth Token Schemas -----------------
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: uuid.UUID
    full_name: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# ----------------- OLT Schemas -----------------
class OLTBase(BaseModel):
    name: str
    ip_address: str
    vendor: OltVendor = OltVendor.GENERIC
    model: Optional[str] = None
    connection_method: ConnectionMethod = ConnectionMethod.SNMP
    snmp_version: str = "v2c"
    snmp_port: int = 161
    ssh_username: Optional[str] = None
    ssh_port: int = 22
    location: Optional[str] = None
    pop_name: Optional[str] = None
    rack_position: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class OLTCreate(OLTBase):
    snmp_community: Optional[str] = None
    snmp_v3_user: Optional[str] = None
    snmp_v3_auth_key: Optional[str] = None
    snmp_v3_priv_key: Optional[str] = None
    ssh_password: Optional[str] = None
    api_url: Optional[str] = None
    api_token: Optional[str] = None

class OLTUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    vendor: Optional[OltVendor] = None
    model: Optional[str] = None
    connection_method: Optional[ConnectionMethod] = None
    snmp_version: Optional[str] = None
    snmp_port: Optional[int] = None
    snmp_community: Optional[str] = None
    snmp_v3_user: Optional[str] = None
    snmp_v3_auth_key: Optional[str] = None
    snmp_v3_priv_key: Optional[str] = None
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_port: Optional[int] = None
    api_url: Optional[str] = None
    api_token: Optional[str] = None
    location: Optional[str] = None
    pop_name: Optional[str] = None
    rack_position: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class OLTRead(OLTBase):
    id: uuid.UUID
    status: DeviceStatus
    cpu_usage: float
    ram_usage: float
    temperature: float
    uptime: Optional[str] = None
    power_status: str
    last_polled_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class OLTConnectionTest(BaseModel):
    olt_id: Optional[uuid.UUID] = None
    vendor: OltVendor
    connection_method: ConnectionMethod
    ip_address: str
    snmp_community: Optional[str] = None
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_port: int = 22

class OLTConnectionTestResult(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None

# ----------------- PON Port Schemas -----------------
class PONPortRead(BaseModel):
    id: uuid.UUID
    olt_id: uuid.UUID
    port_number: str
    name: Optional[str] = None
    admin_status: str
    oper_status: str
    onu_total: int
    onu_online: int
    tx_power: float
    rx_power: float
    rx_utilization: float
    tx_utilization: float
    crc_errors: int
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------- ONU Schemas -----------------
class ONURead(BaseModel):
    id: uuid.UUID
    olt_id: uuid.UUID
    olt_name: Optional[str] = None
    pon_port_id: uuid.UUID
    pon_port_number: Optional[str] = None
    onu_index: int
    serial_number: str
    mac_address: Optional[str] = None
    customer_id: Optional[str] = None
    username: Optional[str] = None
    vlan: Optional[int] = None
    ip_address: Optional[str] = None
    model: Optional[str] = None
    status: OnuStatus
    rx_power: float
    tx_power: float
    distance: float
    traffic_usage: float
    uptime: Optional[str] = None
    last_online_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True

class ONUUpdate(BaseModel):
    customer_id: Optional[str] = None
    username: Optional[str] = None
    vlan: Optional[int] = None

class ONUOperation(BaseModel):
    action: str  # 'reboot', 'enable', 'disable', 'change_vlan'
    vlan: Optional[int] = None

class BulkONUOperation(BaseModel):
    onu_ids: List[uuid.UUID]
    action: str  # 'reboot', 'enable', 'disable'
    vlan: Optional[int] = None

# ----------------- Alarm Schemas -----------------
class AlarmRead(BaseModel):
    id: uuid.UUID
    olt_id: Optional[uuid.UUID] = None
    olt_name: Optional[str] = None
    onu_id: Optional[uuid.UUID] = None
    onu_serial: Optional[str] = None
    alarm_type: AlarmType
    severity: AlarmSeverity
    message: str
    is_active: bool
    raised_at: datetime
    cleared_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ----------------- Audit Log Schemas -----------------
class AuditLogRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: Optional[str] = None
    action: str
    details: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True

# ----------------- Metric History Schemas -----------------
class MetricPoint(BaseModel):
    timestamp: datetime
    value: float

class MetricSeries(BaseModel):
    metric_name: str
    data: List[MetricPoint]
