#Status calculation logic
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

class MonitorStatus:
    UP="UP"
    DOWN="DOWN"
    DEGRADED="DEGRADED"
    UNKNOWN="UNKNOWN"
def calculate_monitor_status(monitor):
    latest_checks=monitor.get_latest_checks(limit=3)
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

def validate_url(url):
    validator=URLValidator(schemes=['http','https'])
    try:
        validator(url)
        return True
    except ValidationError:
        return False