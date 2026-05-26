from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# ----------------- Driver Return Datatypes -----------------

class SystemMetrics(BaseModel):
    status: str = "ONLINE"  # ONLINE, OFFLINE, DEGRADED
    cpu_usage: float = 0.0  # Percentage (0.0 to 100.0)
    ram_usage: float = 0.0  # Percentage
    temperature: float = 0.0  # Celsius
    uptime: str = "Unknown"
    power_status: str = "AC Normal"

class PortMetrics(BaseModel):
    port_number: str  # e.g. "0/1"
    name: Optional[str] = None
    admin_status: str = "UP"  # UP, DOWN
    oper_status: str = "UP"   # UP, DOWN
    tx_power: float = 0.0     # dBm
    rx_power: float = 0.0     # dBm
    rx_utilization: float = 0.0  # bps (inbound)
    tx_utilization: float = 0.0  # bps (outbound)
    crc_errors: int = 0
    onu_total: int = 0
    onu_online: int = 0

class OnuMetrics(BaseModel):
    onu_index: int
    serial_number: str
    mac_address: Optional[str] = None
    status: str  # ONLINE, OFFLINE, LOS, DYING_GASP
    rx_power: float = 0.0   # Signal at OLT (dBm)
    tx_power: float = 0.0   # Signal at ONU (dBm)
    distance: float = 0.0   # Meters
    uptime: Optional[str] = None
    last_online_at: Optional[str] = None
    vlan: Optional[int] = None
    ip_address: Optional[str] = None
    model: Optional[str] = None

# ----------------- Base Driver Class -----------------

class BaseOLTDriver(ABC):
    def __init__(self, ip_address: str, **kwargs):
        self.ip_address = ip_address
        self.snmp_community = kwargs.get("snmp_community", "public")
        self.snmp_port = kwargs.get("snmp_port", 161)
        self.snmp_version = kwargs.get("snmp_version", "v2c")
        
        self.ssh_username = kwargs.get("ssh_username")
        self.ssh_password = kwargs.get("ssh_password")
        self.ssh_port = kwargs.get("ssh_port", 22)
        
        self.api_url = kwargs.get("api_url")
        self.api_token = kwargs.get("api_token")

    @abstractmethod
    async def test_connection(self) -> bool:
        """Verifies if the OLT is reachable via SNMP/SSH/API."""
        pass

    @abstractmethod
    async def get_system_metrics(self) -> SystemMetrics:
        """Retrieve overall CPU, RAM, Temperature, and power status."""
        pass

    @abstractmethod
    async def get_pon_ports(self) -> List[PortMetrics]:
        """Retrieve inventory and real-time statistics of all PON ports."""
        pass

    @abstractmethod
    async def get_onus(self) -> List[OnuMetrics]:
        """Retrieve all ONUs registered on the OLT."""
        pass

    @abstractmethod
    async def reboot_onu(self, port_number: str, onu_index: int) -> bool:
        """Reboot an ONU."""
        pass

    @abstractmethod
    async def set_onu_admin_status(self, port_number: str, onu_index: int, enable: bool) -> bool:
        """Enable or disable an ONU administratively."""
        pass

    @abstractmethod
    async def change_onu_vlan(self, port_number: str, onu_index: int, vlan: int) -> bool:
        """Modify the bridge/management VLAN of a configured ONU."""
        pass
