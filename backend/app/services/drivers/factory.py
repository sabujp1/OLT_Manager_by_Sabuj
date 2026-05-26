from typing import Dict, Any, Type
from app.models.models import OltVendor
from app.services.drivers.base import BaseOLTDriver
from app.services.drivers.generic import GenericSnmpDriver
from app.services.drivers.huawei import HuaweiDriver
from app.services.drivers.zte import ZteDriver
from app.services.drivers.bdcom import BdcomDriver
from app.services.drivers.vsol import VsolDriver

class OLTDriverFactory:
    """Factory class to dynamically instantiate the correct OLT vendor driver."""

    _drivers_map: dict[OltVendor, Type[BaseOLTDriver]] = {
        OltVendor.HUAWEI: HuaweiDriver,
        OltVendor.ZTE: ZteDriver,
        OltVendor.BDCOM: BdcomDriver,
        OltVendor.VSOL: VsolDriver,
        # Default fallback for CData, Nokia, FiberHome, Raisecom, Ubiquiti, etc. if specific driver is absent
        OltVendor.CDATA: VsolDriver, # CDATA shares similar SNMP tables to VSOL/Cortina
        OltVendor.GENERIC: GenericSnmpDriver,
    }

    @classmethod
    def get_driver(cls, vendor: OltVendor, ip_address: str, **kwargs) -> BaseOLTDriver:
        """Returns instantiated vendor driver."""
        driver_cls = cls._drivers_map.get(vendor, GenericSnmpDriver)
        return driver_cls(ip_address=ip_address, **kwargs)
