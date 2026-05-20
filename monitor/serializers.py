from rest_framework import serializers
from .models import URLMonitor,HealthCheckResult
from .utils import calculate_monitor_status


class URLMonitorSerializer(serializers.ModelSerializer):
    current_status=serializers.SerializerMethodField()
    last_checked_at=serializers.SerializerMethodField()

    class Meta:
        model=URLMonitor
        fields=[
            'id','name','url',
            'check_interval_seconds','is_active',
            'current_status','last_checked_at',
            'created_at','updated_at'
        ]
        read_only_fields=[
            'id','current_status','last_checked_at',
            'created_at','updated_at'
        ]
    
    def get_current_status(self,obj):
        return calculate_monitor_status(obj)
    
    def get_last_checked_at(self,obj):
        last_check=obj.results.first()
        return last_check.checked_at if last_check else None
    
    def validate_url(self,value):
        if self.instance is None:
            if URLMonitor.objects.filter(url=value).exists():
                raise serializers.ValidationError(
                    "A monitor with this URL exists"
                )
        return value

class URLMonitorListSerializer(serializers.ModelSerializer):
    current_status=serializers.SerializerMethodField()
    last_checked_at=serializers.SerializerMethodField()
    total_checks=serializers.SerializerMethodField()

    class Meta:
        model=URLMonitor
        #list of model fields that should be included in the serialized output
        fields=[
            'id','name','url','is_active',
            'current_status','last_checked_at','total_checks'
        ]
    
    def get_current_status(self,obj):
        return calculate_monitor_status(obj)
    
    def get_last_checked_at(self,obj):
        last_check=obj.results.first()
        return last_check.checked_at if last_check else None
        
    def get_total_checks(self,obj):
        return obj.results.count()
    
class HealthCheckResultSerializer(serializers.ModelSerializer):
    monitor_name=serializers.CharField(source='monitor.name',read_only=True)
    
    class Meta:
        model=HealthCheckResult
        fields=[
            'id','monitor','monitor_name','status_code',
            'response_time_ms','is_success','error_message',
            'checked_at'
        ]
        read_only_fields=fields

class LatestCheckSerializer(HealthCheckResultSerializer):
    class Meta(HealthCheckResultSerializer.Meta):
        pass