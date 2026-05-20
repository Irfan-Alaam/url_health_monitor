from django.core.management.base import BaseCommand
from monitor.models import URLMonitor
from monitor.tasks import check_url_health


class Command(BaseCommand):
    help = "Queue health checks for all active monitors"

    def handle(self):
        active_monitors = URLMonitor.objects.filter(is_active=True)

        count = 0

        for monitor in active_monitors:
            check_url_health.delay(monitor.id)
            count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Queued health checks for {count} active monitors."
            )
        )