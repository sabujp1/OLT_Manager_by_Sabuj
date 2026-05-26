import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from sqlalchemy import BigInteger

# Roles for RBAC
class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    NOC_ENGINEER = "NOC_ENGINEER"
    READ_ONLY = "READ_ONLY"
    CLIENT_VIEWER = "CLIENT_VIEWER"

# Device Statuses
class DeviceStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"

class OnuStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    LOS = "LOS"
    DYING_GASP = "DYING_GASP"

# OLT Vendors
class OltVendor(str, Enum):
    HUAWEI = "HUAWEI"
    ZTE = "ZTE"
    BDCOM = "BDCOM"
    VSOL = "VSOL"
    CDATA = "CDATA"
    NOKIA = "NOKIA"
    FIBERHOME = "FIBERHOME"
    RAISECOM = "RAISECOM"
    UBIQUITI = "UBIQUITI"
    GENERIC = "GENERIC"

# OLT Connection Methods
class ConnectionMethod(str, Enum):
    SNMP = "SNMP"
    SSH = "SSH"
    TELNET = "TELNET"
    API = "API"

# Alarm Severities and Types
class AlarmSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    WARNING = "WARNING"
    INFO = "INFO"

class AlarmType(str, Enum):
    FIBER_CUT = "FIBER_CUT"
    LOS = "LOS"
    DYING_GASP = "DYING_GASP"
    HIGH_CPU = "HIGH_CPU"
    HIGH_TEMP = "HIGH_TEMP"
    PSU_FAILURE = "PSU_FAILURE"
    FAN_FAILURE = "FAN_FAILURE"
    OFFLINE = "OFFLINE"
    ONU_FLAP = "ONU_FLAP"

# ----------------- Database Models -----------------

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    role: UserRole = Field(default=UserRole.READ_ONLY, nullable=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    audit_logs: List["AuditLog"] = Relationship(back_populates="user")


class OLT(SQLModel, table=True):
    __tablename__ = "olts"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str = Field(index=True, nullable=False)
    ip_address: str = Field(unique=True, index=True, nullable=False)
    vendor: OltVendor = Field(default=OltVendor.GENERIC, nullable=False)
    model: Optional[str] = Field(default=None)
    connection_method: ConnectionMethod = Field(default=ConnectionMethod.SNMP, nullable=False)
    
    # Credentials (Stored Encrypted using AES-256)
    snmp_version: str = Field(default="v2c")
    snmp_port: int = Field(default=161)
    snmp_community: Optional[str] = Field(default=None)  # Encrypted
    snmp_v3_user: Optional[str] = Field(default=None)
    snmp_v3_auth_key: Optional[str] = Field(default=None)  # Encrypted
    snmp_v3_priv_key: Optional[str] = Field(default=None)  # Encrypted
    
    ssh_username: Optional[str] = Field(default=None)
    ssh_password: Optional[str] = Field(default=None)  # Encrypted
    ssh_port: int = Field(default=22)
    
    api_url: Optional[str] = Field(default=None)
    api_token: Optional[str] = Field(default=None)  # Encrypted
    
    # Geographical & Physical details
    location: Optional[str] = Field(default=None)
    pop_name: Optional[str] = Field(default=None)
    rack_position: Optional[str] = Field(default=None)
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
    
    # Live Telemetry Metrics
    status: DeviceStatus = Field(default=DeviceStatus.OFFLINE)
    cpu_usage: float = Field(default=0.0)
    ram_usage: float = Field(default=0.0)
    temperature: float = Field(default=0.0)
    uptime: Optional[str] = Field(default=None)
    power_status: str = Field(default="AC Normal")
    last_polled_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    pon_ports: List["PONPort"] = Relationship(back_populates="olt", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    onus: List["ONU"] = Relationship(back_populates="olt", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    alarms: List["Alarm"] = Relationship(back_populates="olt", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class PONPort(SQLModel, table=True):
    __tablename__ = "pon_ports"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    olt_id: uuid.UUID = Field(foreign_key="olts.id", index=True, nullable=False)
    port_number: str = Field(index=True, nullable=False)  # e.g., '0/1' or '1/1/1'
    name: Optional[str] = Field(default=None)
    admin_status: str = Field(default="UP")  # UP/DOWN
    oper_status: str = Field(default="UP")  # UP/DOWN
    
    # Port metrics
    onu_total: int = Field(default=0)
    onu_online: int = Field(default=0)
    tx_power: float = Field(default=0.0)  # Optical power output (dBm)
    rx_power: float = Field(default=0.0)  # Optical power input (dBm)
    rx_utilization: float = Field(default=0.0)  # inbound bandwidth (bps)
    tx_utilization: float = Field(default=0.0)  # outbound bandwidth (bps)
    crc_errors: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    olt: OLT = Relationship(back_populates="pon_ports")
    onus: List["ONU"] = Relationship(back_populates="pon_port", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class ONU(SQLModel, table=True):
    __tablename__ = "onus"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    olt_id: uuid.UUID = Field(foreign_key="olts.id", index=True, nullable=False)
    pon_port_id: uuid.UUID = Field(foreign_key="pon_ports.id", index=True, nullable=False)
    onu_index: int = Field(index=True, nullable=False)  # ONU Index ID (e.g. 1-128)
    
    # Identity (Searchable indexes)
    serial_number: str = Field(unique=True, index=True, nullable=False)  # GPON Serial e.g., HWTC1234ABCD
    mac_address: Optional[str] = Field(default=None, index=True)
    customer_id: Optional[str] = Field(default=None, index=True)
    username: Optional[str] = Field(default=None, index=True)
    vlan: Optional[int] = Field(default=None, index=True)
    ip_address: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    
    # Telemetry
    status: OnuStatus = Field(default=OnuStatus.OFFLINE)
    rx_power: float = Field(default=0.0)  # Signal level at OLT (dBm)
    tx_power: float = Field(default=0.0)  # Signal level at ONU (dBm)
    distance: float = Field(default=0.0)  # Distance in meters
    traffic_usage: float = Field(default=0.0)  # Bytes or bps
    uptime: Optional[str] = Field(default=None)
    last_online_at: Optional[datetime] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    olt: OLT = Relationship(back_populates="onus")
    pon_port: PONPort = Relationship(back_populates="onus")
    alarms: List["Alarm"] = Relationship(back_populates="onu", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class Alarm(SQLModel, table=True):
    __tablename__ = "alarms"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    olt_id: Optional[uuid.UUID] = Field(default=None, foreign_key="olts.id", index=True)
    onu_id: Optional[uuid.UUID] = Field(default=None, foreign_key="onus.id", index=True)
    
    alarm_type: AlarmType = Field(index=True, nullable=False)
    severity: AlarmSeverity = Field(default=AlarmSeverity.WARNING, nullable=False)
    message: str = Field(nullable=False)
    is_active: bool = Field(default=True, index=True)
    
    raised_at: datetime = Field(default_factory=datetime.utcnow)
    cleared_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    olt: Optional[OLT] = Relationship(back_populates="alarms")
    onu: Optional[ONU] = Relationship(back_populates="alarms")


class MetricHistory(SQLModel, table=True):
    __tablename__ = "metrics_history"
    
    # Use BigInteger for primary key for telemetry scaling
    id: Optional[int] = Field(
        default=None, 
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    target_type: str = Field(index=True, nullable=False)  # 'OLT', 'PON_PORT', 'ONU'
    target_id: uuid.UUID = Field(index=True, nullable=False)
    metric_name: str = Field(index=True, nullable=False)  # 'cpu', 'ram', 'temp', 'rx_power', 'utilization_in', 'utilization_out'
    value: float = Field(nullable=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    action: str = Field(nullable=False)  # e.g., 'REBOOT_ONU', 'DISABLE_ONU', 'UPDATE_OLT'
    details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="audit_logs")
