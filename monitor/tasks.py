import requests, time, logging
from celery import shared_task
from .config import TIMEOUT,MAX_RETRIES

logger=logging.getLogger(__name__)

@shared_task(bind=True, max_retries=MAX_RETRIES)
def check_url_health(self,monitor_id):
    from .models import URLMonitor,HealthCheckResult
    try:
        monitor=URLMonitor.objects.get(id=monitor_id)
        if not monitor.is_active:
            logger.info(f"Inactive monitor: {monitor.name}, skipping...")
            return
        
        status_code=None
        response_time_ms=0.0
        is_success=False
        error_message=None

        start = time.monotonic()

        try:
            response=requests.get(monitor.url,timeout=TIMEOUT,allow_redirects=True,headers={'User-Agent': 'URL_Health'})
            response_time_ms=(time.monotonic()-start)*1000
            status_code=response.status_code
            is_success=200<=status_code<400
        
        except requests.exceptions.Timeout:
            response_time_ms=(time.monotonic()-start)*1000
            error_message=f"Request timeout: {TIMEOUT} seconds"
        
        except requests.exceptions.ConnectionError as e:
            response_time_ms=(time.monotonic()-start)*1000
            error_message = f"Connection error: {str(e)}"
            
        except requests.exceptions.RequestException as e:
            response_time_ms=(time.monotonic()-start)*1000
            error_message = f"Request failed: {str(e)}"
            
        except Exception as e:
            response_time_ms=(time.monotonic()-start)*1000
            error_message = f"Unexpected error: {str(e)[:200]}"

        HealthCheckResult.objects.create(
            monitor=monitor,
            status_code=status_code,
            response_time_ms=round(response_time_ms,2),
            is_success = is_success,
            error_message=error_message
        )

        logger.info(f"Checked {monitor.url}->status={status_code},success={'OK' if is_success else 'FAIL'},time = {response_time_ms}ms")

        return {
            "monitor_id": monitor_id,
            "url": monitor.url,
            "status_code": status_code,
            "is_success": is_success,
            "response_time_ms": round(response_time_ms, 2),
            "error": error_message
        }

    except URLMonitor.DoesNotExist:
        logger.error(f"Monitor with ID {monitor_id} not found")
        return {"status": "error", "reason": "monitor_not_found"}
    
    except Exception as e:
        logger.exception(f"Task failed for monitor {monitor_id}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {"status": "error", "reason": str(e)}

@shared_task
def check_all_active_urls():
    from .models import URLMonitor
    active_monitors=URLMonitor.objects.filter(is_active=True)
    tasks_queued=0

    for monitor in active_monitors:
        check_url_health.delay(monitor.id)
        tasks_queued+=1
    
    logger.info(f"Queued health checks for {tasks_queued} active monitors")

    return {"total_active_monitors":tasks_queued,
            "tasks_queued":tasks_queued}