import asyncio
import json
import logging
from datetime import datetime
import redis
from celery import shared_task
from sqlmodel import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import async_session_maker
from app.core.security import encryptor
from app.models.models import OLT, PONPort, ONU, Alarm, AlarmType, AlarmSeverity, DeviceStatus, OnuStatus, MetricHistory
from app.services.drivers.factory import OLTDriverFactory

logger = logging.getLogger(__name__)

# Sync Redis client for Celery tasks
redis_client = redis.from_url(settings.REDIS_URL)

def run_async(coro):
    """Executes an async coroutine synchronously inside Celery."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

def publish_ws_event(event_type: str, data: dict):
    """Publishes an event to Redis Pub/Sub for WebSockets."""
    payload = {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }
    redis_client.publish("noc_events", json.dumps(payload))

# ----------------- Celery Task Definitions -----------------

@shared_task(name="app.services.polling.tasks.fast_poll_olts")
def fast_poll_olts():
    """Polls OLT CPU, RAM, Temp, and general availability (Every 30s)."""
    return run_async(_async_fast_poll_olts())

@shared_task(name="app.services.polling.tasks.metric_poll_ports")
def metric_poll_ports():
    """Polls PON port traffic utilization and optical power (Every 2m)."""
    return run_async(_async_metric_poll_ports())

@shared_task(name="app.services.polling.tasks.inventory_sync_onus")
def inventory_sync_onus():
    """Syncs ONU states, distances, serials, and power levels (Every 10m)."""
    return run_async(_async_inventory_sync_onus())

# ----------------- Async Polling Logic -----------------

async def _async_fast_poll_olts():
    logger.info("Starting fast poll of all OLTs...")
    async with async_session_maker() as db:
        result = await db.execute(select(OLT))
        olts = result.scalars().all()
        
        for olt in olts:
            try:
                # Decrypt community and SSH password if present
                community = encryptor.decrypt(olt.snmp_community) if olt.snmp_community else "public"
                ssh_pass = encryptor.decrypt(olt.ssh_password) if olt.ssh_password else None
                
                # Instantiate driver
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
                
                # Ping / SNMP Get metrics
                is_connected = await driver.test_connection()
                
                if is_connected:
                    sys_metrics = await driver.get_system_metrics()
                    
                    olt.status = DeviceStatus.ONLINE
                    olt.cpu_usage = sys_metrics.cpu_usage
                    olt.ram_usage = sys_metrics.ram_usage
                    olt.temperature = sys_metrics.temperature
                    olt.uptime = sys_metrics.uptime
                    olt.power_status = sys_metrics.power_status
                    olt.last_polled_at = datetime.utcnow()
                    
                    db.add(olt)
                    
                    # Record metric history
                    cpu_history = MetricHistory(target_type="OLT", target_id=olt.id, metric_name="cpu", value=sys_metrics.cpu_usage)
                    ram_history = MetricHistory(target_type="OLT", target_id=olt.id, metric_name="ram", value=sys_metrics.ram_usage)
                    temp_history = MetricHistory(target_type="OLT", target_id=olt.id, metric_name="temp", value=sys_metrics.temperature)
                    db.add_all([cpu_history, ram_history, temp_history])
                    
                    # Clear active unreachable alarm if any
                    alarm_q = await db.execute(
                        select(Alarm).where(
                            Alarm.olt_id == olt.id,
                            Alarm.alarm_type == AlarmType.OLT_UNREACHABLE,
                            Alarm.is_active == True
                        )
                    )
                    active_alarm = alarm_q.scalars().first()
                    if active_alarm:
                        active_alarm.is_active = False
                        active_alarm.cleared_at = datetime.utcnow()
                        db.add(active_alarm)
                        
                        publish_ws_event("alarm_cleared", {
                            "alarm_id": str(active_alarm.id),
                            "olt_id": str(olt.id),
                            "olt_name": olt.name,
                            "type": active_alarm.alarm_type
                        })
                    
                    # High CPU/Temp alerts
                    if sys_metrics.cpu_usage > 85.0:
                        await _raise_olt_alarm(db, olt, AlarmType.HIGH_CPU, AlarmSeverity.CRITICAL, f"OLT High CPU Usage: {sys_metrics.cpu_usage}%")
                    if sys_metrics.temperature > 65.0:
                        await _raise_olt_alarm(db, olt, AlarmType.HIGH_TEMP, AlarmSeverity.MAJOR, f"OLT High Temperature: {sys_metrics.temperature}°C")
                        
                else:
                    await _handle_olt_offline(db, olt)

            except Exception as e:
                logger.error(f"Failed to poll OLT {olt.name} ({olt.ip_address}): {str(e)}")
                await _handle_olt_offline(db, olt)
                
        await db.commit()
    logger.info("Fast poll cycle completed.")


async def _async_metric_poll_ports():
    logger.info("Starting PON metrics poll...")
    async with async_session_maker() as db:
        # Fetch OLTs with their preloaded PON Ports
        result = await db.execute(select(OLT).options(selectinload(OLT.pon_ports)))
        olts = result.scalars().all()
        
        for olt in olts:
            if olt.status != DeviceStatus.ONLINE:
                continue
            try:
                community = encryptor.decrypt(olt.snmp_community) if olt.snmp_community else "public"
                driver = OLTDriverFactory.get_driver(
                    vendor=olt.vendor,
                    ip_address=olt.ip_address,
                    snmp_community=community,
                    snmp_port=olt.snmp_port
                )
                
                # Fetch port traffic and status
                driver_ports = await driver.get_pon_ports()
                
                # Update existing ports or add missing ones
                db_ports = {p.port_number: p for p in olt.pon_ports}
                for dp in driver_ports:
                    port = db_ports.get(dp.port_number)
                    if not port:
                        port = PONPort(olt_id=olt.id, port_number=dp.port_number)
                        db.add(port)
                    
                    port.name = dp.name
                    port.admin_status = dp.admin_status
                    port.oper_status = dp.oper_status
                    port.tx_power = dp.tx_power
                    port.rx_power = dp.rx_power
                    port.rx_utilization = dp.rx_utilization
                    port.tx_utilization = dp.tx_utilization
                    port.crc_errors = dp.crc_errors
                    port.updated_at = datetime.utcnow()
                    
                    # Record port metrics history
                    rx_util_history = MetricHistory(target_type="PON_PORT", target_id=port.id, metric_name="utilization_in", value=dp.rx_utilization)
                    tx_util_history = MetricHistory(target_type="PON_PORT", target_id=port.id, metric_name="utilization_out", value=dp.tx_utilization)
                    db.add_all([rx_util_history, tx_util_history])
                    
                    # Alert if CRC Errors growing rapidly
                    if dp.crc_errors > 100:
                        await _raise_olt_alarm(db, olt, AlarmType.HIGH_BANDWIDTH, AlarmSeverity.WARNING, f"High CRC errors detected on PON {dp.port_number}: {dp.crc_errors}")

            except Exception as e:
                logger.error(f"Failed to poll PON metrics on OLT {olt.name}: {str(e)}")
                
        await db.commit()
    logger.info("PON metrics poll cycle completed.")


async def _async_inventory_sync_onus():
    logger.info("Starting full ONU sync cycle...")
    async with async_session_maker() as db:
        result = await db.execute(
            select(OLT).options(
                selectinload(OLT.pon_ports),
                selectinload(OLT.onus)
            )
        )
        olts = result.scalars().all()
        
        for olt in olts:
            if olt.status != DeviceStatus.ONLINE:
                continue
            try:
                community = encryptor.decrypt(olt.snmp_community) if olt.snmp_community else "public"
                driver = OLTDriverFactory.get_driver(
                    vendor=olt.vendor,
                    ip_address=olt.ip_address,
                    snmp_community=community,
                    snmp_port=olt.snmp_port
                )
                
                # Fetch all registered ONUs
                driver_onus = await driver.get_onus()
                
                # Preload existing ONUs and PON ports for local lookup
                db_onus = {onu.serial_number: onu for onu in olt.onus}
                db_ports = {p.port_number: p for p in olt.pon_ports}
                
                # Track online count per PON port
                port_counts = {p.id: {"total": 0, "online": 0} for p in olt.pon_ports}
                
                for d_onu in driver_onus:
                    # Find parent PON port ID
                    port_id = None
                    # For simplicity, assign to the first PON port if vendor driver didn't specify, or find by naming convention
                    # Most drivers put correct details. If port is missing, create a placeholder
                    target_port_num = "0/1" # Default fallback
                    # In a real driver, d_onu has interface data or we match it. We'll find port by mapping
                    # Let's check matching port:
                    matching_port = next((p for p in olt.pon_ports if p.port_number in d_onu.serial_number), None)
                    if not matching_port and olt.pon_ports:
                        matching_port = olt.pon_ports[0]
                    
                    if matching_port:
                        port_id = matching_port.id
                    else:
                        continue
                    
                    onu = db_onus.get(d_onu.serial_number)
                    if not onu:
                        # Register New ONU found dynamically
                        onu = ONU(
                            olt_id=olt.id,
                            pon_port_id=port_id,
                            onu_index=d_onu.onu_index,
                            serial_number=d_onu.serial_number,
                            status=OnuStatus(d_onu.status)
                        )
                        db.add(onu)
                        
                        # Trigger alert for new dynamic ONU discovery
                        publish_ws_event("onu_discovered", {
                            "olt_id": str(olt.id),
                            "olt_name": olt.name,
                            "serial_number": d_onu.serial_number,
                            "port": matching_port.port_number
                        })
                    
                    # Update status transition
                    old_status = onu.status
                    onu.status = OnuStatus(d_onu.status)
                    onu.rx_power = d_onu.rx_power
                    onu.tx_power = d_onu.tx_power
                    onu.distance = d_onu.distance
                    onu.vlan = d_onu.vlan or onu.vlan
                    onu.model = d_onu.model
                    onu.updated_at = datetime.utcnow()
                    
                    if onu.status == OnuStatus.ONLINE:
                        onu.last_online_at = datetime.utcnow()
                        port_counts[port_id]["online"] += 1
                    
                    port_counts[port_id]["total"] += 1
                    
                    # Record metric history
                    rx_sig_history = MetricHistory(target_type="ONU", target_id=onu.id, metric_name="rx_power", value=d_onu.rx_power)
                    db.add(rx_sig_history)
                    
                    # Trigger alarms for critical events
                    if old_status == OnuStatus.ONLINE and onu.status == OnuStatus.OFFLINE:
                        await _raise_onu_alarm(db, olt, onu, AlarmType.OFFLINE, AlarmSeverity.WARNING, f"ONU {onu.serial_number} went offline.")
                    elif old_status == OnuStatus.ONLINE and onu.status == OnuStatus.LOS:
                        await _raise_onu_alarm(db, olt, onu, AlarmType.LOS, AlarmSeverity.CRITICAL, f"ONU {onu.serial_number} Loss of Signal (LOS) detected.")
                    elif old_status == OnuStatus.ONLINE and onu.status == OnuStatus.DYING_GASP:
                        await _raise_onu_alarm(db, olt, onu, AlarmType.DYING_GASP, AlarmSeverity.CRITICAL, f"ONU {onu.serial_number} Dying Gasp (Power failure) alarm raised.")
                    elif onu.status == OnuStatus.ONLINE and old_status != OnuStatus.ONLINE:
                        # Clear active alarms
                        await _clear_onu_alarms(db, onu)
                
                # Update PON Port online/total counters
                for port_id, counts in port_counts.items():
                    port = db_ports.get(next(p.port_number for p in olt.pon_ports if p.id == port_id))
                    if port:
                        port.onu_total = counts["total"]
                        port.onu_online = counts["online"]
                        db.add(port)

            except Exception as e:
                logger.error(f"Failed to sync ONU inventory on OLT {olt.name}: {str(e)}")
                
        await db.commit()
    logger.info("ONU sync cycle completed.")

# ----------------- Alarm Helpers -----------------

async def _handle_olt_offline(db, olt: OLT):
    """Updates OLT state to OFFLINE and raises Alarm."""
    olt.status = DeviceStatus.OFFLINE
    olt.cpu_usage = 0.0
    olt.ram_usage = 0.0
    olt.temperature = 0.0
    db.add(olt)
    
    # Check if active alarm already exists
    alarm_q = await db.execute(
        select(Alarm).where(
            Alarm.olt_id == olt.id,
            Alarm.alarm_type == AlarmType.OLT_UNREACHABLE,
            Alarm.is_active == True
        )
    )
    if not alarm_q.scalars().first():
        alarm = Alarm(
            olt_id=olt.id,
            alarm_type=AlarmType.OLT_UNREACHABLE,
            severity=AlarmSeverity.CRITICAL,
            message=f"OLT {olt.name} is unreachable at {olt.ip_address}",
            is_active=True
        )
        db.add(alarm)
        await db.flush() # Populate ID
        
        publish_ws_event("alarm_raised", {
            "alarm_id": str(alarm.id),
            "olt_id": str(olt.id),
            "olt_name": olt.name,
            "type": alarm.alarm_type,
            "severity": alarm.severity,
            "message": alarm.message,
            "raised_at": alarm.raised_at.isoformat()
        })


async def _raise_olt_alarm(db, olt: OLT, alarm_type: AlarmType, severity: AlarmSeverity, message: str):
    """Raises a system-level alarm for an OLT."""
    alarm_q = await db.execute(
        select(Alarm).where(
            Alarm.olt_id == olt.id,
            Alarm.alarm_type == alarm_type,
            Alarm.is_active == True
        )
    )
    if not alarm_q.scalars().first():
        alarm = Alarm(
            olt_id=olt.id,
            alarm_type=alarm_type,
            severity=severity,
            message=message,
            is_active=True
        )
        db.add(alarm)
        await db.flush()
        
        publish_ws_event("alarm_raised", {
            "alarm_id": str(alarm.id),
            "olt_id": str(olt.id),
            "olt_name": olt.name,
            "type": alarm.alarm_type,
            "severity": alarm.severity,
            "message": alarm.message,
            "raised_at": alarm.raised_at.isoformat()
        })


async def _raise_onu_alarm(db, olt: OLT, onu: ONU, alarm_type: AlarmType, severity: AlarmSeverity, message: str):
    """Raises an alarm for a specific ONU."""
    alarm_q = await db.execute(
        select(Alarm).where(
            Alarm.onu_id == onu.id,
            Alarm.alarm_type == alarm_type,
            Alarm.is_active == True
        )
    )
    if not alarm_q.scalars().first():
        alarm = Alarm(
            olt_id=olt.id,
            onu_id=onu.id,
            alarm_type=alarm_type,
            severity=severity,
            message=message,
            is_active=True
        )
        db.add(alarm)
        await db.flush()
        
        publish_ws_event("alarm_raised", {
            "alarm_id": str(alarm.id),
            "olt_id": str(olt.id),
            "olt_name": olt.name,
            "onu_id": str(onu.id),
            "onu_serial": onu.serial_number,
            "type": alarm.alarm_type,
            "severity": alarm.severity,
            "message": alarm.message,
            "raised_at": alarm.raised_at.isoformat()
        })


async def _clear_onu_alarms(db, onu: ONU):
    """Clears all active alarms for an ONU."""
    alarm_q = await db.execute(
        select(Alarm).where(
            Alarm.onu_id == onu.id,
            Alarm.is_active == True
        )
    )
    active_alarms = alarm_q.scalars().all()
    for alarm in active_alarms:
        alarm.is_active = False
        alarm.cleared_at = datetime.utcnow()
        db.add(alarm)
        
        publish_ws_event("alarm_cleared", {
            "alarm_id": str(alarm.id),
            "onu_id": str(onu.id),
            "onu_serial": onu.serial_number,
            "type": alarm.alarm_type
        })
