from django.db import models
from django.core.validators import URLValidator,MinValueValidator

class URLMonitor(models.Model):
    name=models.CharField(max_length=50)
    url=models.URLField(validators=[URLValidator(schemes=['http', 'https'])],unique=True)
    check_interval_seconds=models.IntegerField(validators=[MinValueValidator(60)])
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class HealthCheckResult(models.Model):
    monitor=models.ForeignKey(URLMonitor,on_delete=models.CASCADE,related_name="results")
    status_code=models.IntegerField(null=True,blank=True)
    response_time_ms=models.FloatField()
    is_success=models.BooleanField()
    error_message=models.TextField(blank=True,null=True)
    checked_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.monitor.name} -> {self.status_code}'
    
    class Meta:
        ordering=['-checked_at']