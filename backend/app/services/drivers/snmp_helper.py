import logging
import asyncio
from typing import List, Dict, Any, Optional
import aiosnmp

logger = logging.getLogger(__name__)

class SnmpHelper:
    """Wrapper around aiosnmp to provide clean, robust, async SNMP operations."""
    
    def __init__(self, host: str, community: str = "public", port: int = 161):
        self.host = host
        self.community = community
        self.port = port

    async def get(self, oids: List[str]) -> Dict[str, Any]:
        """Performs async SNMP GET for a list of OIDs."""
        results = {}
        try:
            async with aiosnmp.Snmp(
                host=self.host, 
                port=self.port, 
                community=self.community,
                timeout=2.0,
                retries=2
            ) as snmp:
                records = await snmp.get(oids)
                for record in records:
                    results[record.oid] = self._decode_value(record.value)
        except Exception as e:
            logger.warning(f"SNMP GET failed on {self.host}: {str(e)}")
        return results

    async def get_single(self, oid: str) -> Optional[Any]:
        """Gets a single OID value."""
        res = await self.get([oid])
        return res.get(oid)

    async def walk(self, base_oid: str) -> Dict[str, Any]:
        """Performs async SNMP WALK/BULKWALK for a base OID."""
        results = {}
        try:
            async with aiosnmp.Snmp(
                host=self.host, 
                port=self.port, 
                community=self.community,
                timeout=4.0,
                retries=2
            ) as snmp:
                records = await snmp.walk(base_oid)
                for record in records:
                    results[record.oid] = self._decode_value(record.value)
        except Exception as e:
            logger.warning(f"SNMP WALK failed on {self.host} for base {base_oid}: {str(e)}")
        return results

    def _decode_value(self, val: Any) -> Any:
        """Helper to decode bytes and parse numbers from SNMP payloads."""
        if isinstance(val, bytes):
            try:
                return val.decode("utf-8")
            except UnicodeDecodeError:
                # If bytes represents a hex-string / MAC address
                return ":".join(f"{b:02x}" for b in val)
        return val
