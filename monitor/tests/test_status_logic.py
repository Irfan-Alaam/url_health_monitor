from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from monitor.models import URLMonitor, HealthCheckResult
from monitor.utils import calculate_monitor_status
from monitor.tasks import check_url_health

class StatusCalculationTests(TestCase):

    def setUp(self):
        self.monitor = URLMonitor.objects.create(
            name="Test Monitor",
            url="https://example.com",
            check_interval_seconds=60
        )

    def create_check(self, success):
        return HealthCheckResult.objects.create(
            monitor=self.monitor,
            status_code=200 if success else 500,
            response_time_ms=100,
            is_success=success
        )

    def test_returns_unknown_when_less_than_3_checks(self):
        self.assertEqual(calculate_monitor_status(self.monitor), "UNKNOWN")
        self.create_check(True)
        self.assertEqual(calculate_monitor_status(self.monitor), "UNKNOWN")

    def test_returns_up_when_last_3_checks_successful(self):
        self.create_check(True)
        self.create_check(True)
        self.create_check(True)
        self.assertEqual(calculate_monitor_status(self.monitor), "UP")

    def test_returns_down_when_last_3_checks_fail(self):
        self.create_check(False)
        self.create_check(False)
        self.create_check(False)
        self.assertEqual(calculate_monitor_status(self.monitor), "DOWN")

    def test_returns_degraded_when_results_are_mixed(self):
        self.create_check(True)
        self.create_check(False)
        self.create_check(True)
        self.assertEqual(calculate_monitor_status(self.monitor), "DEGRADED")

    def test_only_last_3_checks_are_used(self):
        self.create_check(False)
        self.create_check(False)
        self.create_check(True)
        self.create_check(True)
        self.create_check(True)
        self.assertEqual(calculate_monitor_status(self.monitor), "UP")


# Api viewset tests
class URLMonitorAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.monitor = URLMonitor.objects.create(
            name="API Monitor",
            url="https://example.com",
            check_interval_seconds=60,
            is_active=True
        )

        self.check = HealthCheckResult.objects.create(
            monitor=self.monitor,
            status_code=200,
            response_time_ms=120,
            is_success=True
        )

    def test_list_monitors(self):
        response = self.client.get("/api/monitors/")
        self.assertEqual(response.status_code, 200)

    def test_create_monitor(self):
        data = {
            "name": "New Monitor",
            "url": "https://google.com",
            "check_interval_seconds": 60,
            "is_active": True
        }

        response = self.client.post("/api/monitors/", data)  # FIXED (removed extra slash)
        self.assertEqual(response.status_code, 201)

    def test_retrieve_monitor(self):
        response = self.client.get(f"/api/monitors/{self.monitor.id}/")
        self.assertEqual(response.status_code, 200)

    def test_latest_check(self):
        response = self.client.get(f"/api/monitors/{self.monitor.id}/latest_check/")
        self.assertEqual(response.status_code, 200)

    def test_checks_list(self):
        response = self.client.get(f"/api/monitors/{self.monitor.id}/checks/")
        self.assertEqual(response.status_code, 200)

    @patch("monitor.views.check_url_health.delay")
    def test_check_now_queues_task(self, mock_delay):
        mock_delay.return_value.id = "task123"

        response = self.client.post(f"/api/monitors/{self.monitor.id}/check_now/")

        self.assertEqual(response.status_code, 202)
        self.assertTrue(mock_delay.called)

    def test_check_now_inactive_monitor(self):
        self.monitor.is_active = False
        self.monitor.save()

        response = self.client.post(f"/api/monitors/{self.monitor.id}/check_now/")
        self.assertEqual(response.status_code, 400)


# Celery tasks tests
class CeleryTaskTests(TestCase):

    def setUp(self):
        self.monitor = URLMonitor.objects.create(
            name="Task Monitor",
            url="https://example.com",
            check_interval_seconds=60,
            is_active=True
        )

    @patch("monitor.tasks.requests.get")
    def test_successful_url_check(self, mock_get):
        mock_response = type("obj", (), {"status_code": 200})
        mock_get.return_value = mock_response

        result = check_url_health(self.monitor.id)

        self.assertEqual(result["is_success"], True)
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(HealthCheckResult.objects.count(), 1)

    @patch("monitor.tasks.requests.get", side_effect=Exception("fail"))
    def test_failed_url_check(self, mock_get):
        result = check_url_health(self.monitor.id)

        self.assertIn("error", result)
        self.assertEqual(HealthCheckResult.objects.count(), 1)

    def test_inactive_monitor_skips(self):
        self.monitor.is_active = False
        self.monitor.save()

        result = check_url_health(self.monitor.id)
        self.assertIsNone(result)

    def test_monitor_not_found(self):
        result = check_url_health(999999)
        self.assertEqual(result["reason"], "monitor_not_found")