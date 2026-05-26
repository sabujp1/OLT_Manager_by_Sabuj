import logging
import re
from typing import List, Dict, Any
from app.services.drivers.base import BaseOLTDriver, SystemMetrics, PortMetrics, OnuMetrics
from app.services.drivers.snmp_helper import SnmpHelper
from app.services.drivers.cli_helper import CliHelper

logger = logging.getLogger(__name__)

class HuaweiDriver(BaseOLTDriver):
    """Huawei MA5600/MA5800 Series GPON OLT Driver."""

    # Huawei Enterprise SNMP MIBs
    OID_CPU_USAGE = "1.3.6.1.4.1.2011.6.1.1.1.3"      # hwEntityCpuUsage
    OID_MEM_USAGE = "1.3.6.1.4.1.2011.6.1.1.1.4"      # hwEntityMemUsage
    OID_TEMPERATURE = "1.3.6.1.4.1.2011.6.1.1.1.2"    # hwEntityTemperature
    OID_SYS_UPTIME = "1.3.6.1.2.1.1.3.0"
    
    # Huawei GPON MIBs
    OID_ONU_SERIAL = "1.3.6.1.4.1.2011.6.128.1.1.2.43.1.9"   # hwGponOnuSn
    OID_ONU_STATUS = "1.3.6.1.4.1.2011.6.128.1.1.2.46.1.15"  # hwGponOnuState (1=online, 2=offline, 5=lost)
    OID_ONU_RX_POWER = "1.3.6.1.4.1.2011.6.128.1.1.2.51.1.4" # hwGponOnuRxOpticalPower (divided by 100 to get dBm)
    OID_ONU_DISTANCE = "1.3.6.1.4.1.2011.6.128.1.1.2.46.1.20" # hwGponOnuDistance (in meters)

    def __init__(self, ip_address: str, **kwargs):
        super().__init__(ip_address, **kwargs)
        self.snmp = SnmpHelper(ip_address, self.snmp_community, self.snmp_port)
        self.cli = CliHelper(ip_address, self.ssh_username, self.ssh_password, self.ssh_port, platform="huawei_vrp")

    async def test_connection(self) -> bool:
        snmp_ok = await self.snmp.get_single(self.OID_SYS_UPTIME) is not None
        if not snmp_ok and self.ssh_username and self.ssh_password:
            return await self.cli.test_ssh_connection()
        return snmp_ok

    async def get_system_metrics(self) -> SystemMetrics:
        # Get active board metrics using walk/get
        cpu_data = await self.snmp.walk(self.OID_CPU_USAGE)
        mem_data = await self.snmp.walk(self.OID_MEM_USAGE)
        temp_data = await self.snmp.walk(self.OID_TEMPERATURE)
        uptime_ticks = await self.snmp.get_single(self.OID_SYS_UPTIME)

        # Huawei stores Board metrics in table format, parse the first active control board (index usually ends in .0.0 or similar)
        cpu = max(cpu_data.values()) if cpu_data else 0.0
        mem = max(mem_data.values()) if mem_data else 0.0
        temp = max(temp_data.values()) if temp_data else 0.0
        
        # Convert uptime
        uptime_str = "Unknown"
        if uptime_ticks:
            seconds = int(uptime_ticks) // 100
            days, seconds = divmod(seconds, 86400)
            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)
            uptime_str = f"{days}d {hours}h {minutes}m"

        return SystemMetrics(
            status="ONLINE" if cpu > 0 else "DEGRADED",
            cpu_usage=float(cpu),
            ram_usage=float(mem),
            temperature=float(temp),
            uptime=uptime_str,
            power_status="AC Normal"
        )

    async def get_pon_ports(self) -> List[PortMetrics]:
        # Walk IF-MIB standard interfaces for description mapping
        descrs = await self.snmp.walk("1.3.6.1.2.1.2.2.1.2")
        oper_statuses = await self.snmp.walk("1.3.6.1.2.1.2.2.1.8")
        
        ports = []
        for oid, descr in descrs.items():
            # Filter Huawei GPON port descriptions like '0/1/2' or 'GPON 0/1/2'
            if "gpon" in descr.lower() or re.match(r"^\d+/\d+/\d+$", descr):
                if_index = oid.split(".")[-1]
                status_val = oper_statuses.get(f"1.3.6.1.2.1.2.2.1.8.{if_index}", 1)
                oper_status = "UP" if status_val == 1 else "DOWN"
                
                ports.append(PortMetrics(
                    port_number=descr,
                    name=descr,
                    admin_status="UP",
                    oper_status=oper_status,
                    tx_power=2.8,  # Default SFP Class C+ power
                    rx_power=-15.0,
                    rx_utilization=0.0,
                    tx_utilization=0.0,
                    crc_errors=0,
                    onu_total=0,
                    onu_online=0
                ))
        return ports

    async def get_onus(self) -> List[OnuMetrics]:
        # Walk Huawei ONU details using dynamic tables
        serials = await self.snmp.walk(self.OID_ONU_SERIAL)
        statuses = await self.snmp.walk(self.OID_ONU_STATUS)
        rx_powers = await self.snmp.walk(self.OID_ONU_RX_POWER)
        distances = await self.snmp.walk(self.OID_ONU_DISTANCE)
        
        onus = []
        for oid, sn in serials.items():
            # OID suffix format: ...<port_index>.<onu_index>
            suffix = oid.replace(self.OID_ONU_SERIAL + ".", "")
            status_val = statuses.get(f"{self.OID_ONU_STATUS}.{suffix}", 2)
            
            # Status decoding: 1=online, 2=offline, 5=lost, others=LOS/DyingGasp
            onu_status = "OFFLINE"
            if status_val == 1:
                onu_status = "ONLINE"
            elif status_val == 5:
                onu_status = "LOS"
            
            # Optical RX Power decoding (raw value is stored multiplied by 100 or as signed offset)
            raw_rx = rx_powers.get(f"{self.OID_ONU_RX_POWER}.{suffix}", 0)
            rx_dbm = 0.0
            if raw_rx and raw_rx != 2147483647: # Out of range value
                # If negative value
                if raw_rx > 100000:
                    rx_dbm = (raw_rx - 4294967296) / 100.0 if raw_rx > 2147483647 else raw_rx / 100.0
                else:
                    rx_dbm = raw_rx / 100.0
            
            dist = float(distances.get(f"{self.OID_ONU_DISTANCE}.{suffix}", 0))
            
            # Split suffix to extract ONU index and port details
            parts = suffix.split(".")
            onu_idx = int(parts[-1]) if parts else 0
            
            onus.append(OnuMetrics(
                onu_index=onu_idx,
                serial_number=sn,
                status=onu_status,
                rx_power=rx_dbm,
                tx_power=1.5,
                distance=dist,
                model="Generic Huawei"
            ))
        return onus

    # CLI Writes (SSH Configuration via Scrapli VRP Driver)
    async def reboot_onu(self, port_number: str, onu_index: int) -> bool:
        # Huawei port number is formatted board/frame/port (e.g. 0/1/2)
        # Commands: 
        # system-view
        # interface gpon 0/1 (where 0/1 is the board/frame interface)
        # ont reboot 2 3 (where 2 is port, 3 is onu_index)
        m = re.match(r"^(\d+)/(\d+)/(\d+)$", port_number.replace("GPON", "").strip())
        if not m:
            logger.error(f"Invalid Huawei port format: {port_number}")
            return False
        
        frame, slot, port = m.groups()
        cmds = [
            "system-view",
            f"interface gpon {frame}/{slot}",
            f"ont reboot {port} {onu_index}",
            "commit"
        ]
        res = await self.cli.execute_commands(cmds)
        return res is not None

    async def set_onu_admin_status(self, port_number: str, onu_index: int, enable: bool) -> bool:
        m = re.match(r"^(\d+)/(\d+)/(\d+)$", port_number.replace("GPON", "").strip())
        if not m:
            return False
        
        frame, slot, port = m.groups()
        action = "activate" if enable else "deactivate"
        cmds = [
            "system-view",
            f"interface gpon {frame}/{slot}",
            f"ont {action} {port} {onu_index}",
            "commit"
        ]
        res = await self.cli.execute_commands(cmds)
        return res is not None

    async def change_onu_vlan(self, port_number: str, onu_index: int, vlan: int) -> bool:
        m = re.match(r"^(\d+)/(\d+)/(\d+)$", port_number.replace("GPON", "").strip())
        if not m:
            return False
        
        frame, slot, port = m.groups()
        # Modifies native VLAN for ONT ethernet interface 1
        cmds = [
            "system-view",
            f"interface gpon {frame}/{slot}",
            f"ont port native-vlan {port} {onu_index} eth 1 vlan {vlan}",
            "commit"
        ]
        res = await self.cli.execute_commands(cmds)
        return res is not None
