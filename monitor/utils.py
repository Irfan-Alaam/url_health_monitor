from .config import LIMIT
class MonitorStatus:
    UP="UP"
    DOWN="DOWN"
    DEGRADED="DEGRADED"
    UNKNOWN="UNKNOWN"
def calculate_monitor_status(monitor):
    latest_checks=list(monitor.results.all()[:LIMIT])
    check_count=len(latest_checks)
    if check_count<3:
        return MonitorStatus.UNKNOWN
    success_status=[check.is_success for check in latest_checks]
    if all(success_status):
        return MonitorStatus.UP
    elif not any(success_status):
        return MonitorStatus.DOWN
    else:
        return MonitorStatus.DEGRADED