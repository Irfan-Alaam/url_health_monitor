from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, decorators
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import URLMonitor,HealthCheckResult
from .serializers import(URLMonitorSerializer,URLMonitorListSerializer,HealthCheckResultSerializer,LatestCheckSerializer)
from .tasks import check_url_health

class URLMonitorViewSet(viewsets.ModelViewSet):
    queryset=URLMonitor.objects.all()
    permission_classes=[AllowAny]

    def get_serializer_class(self):
        if self.action=='list':
            return URLMonitorListSerializer
        return URLMonitorSerializer
    
    def get_queryset(self):
        queryset=URLMonitor.objects.all()
        if self.action=='list':
            queryset=self.queryset.prefetch_related('results')
        return queryset

    @decorators.action(detail=True,methods=['get'])
    def latest_check(self,request,pk=None):
        monitor=self.get_object()
        latest_check=monitor.results.first()

        if not self.latest_check:
            return Response({"details":"No health check performed"},status=status.HTTP_404_NOT_FOUND),
            serializer=LatestCheckSerializer(latest_check)
            return Response(serializer.data)
        
    @decorators.action(detail=True,methods=['get'])
    def checks(self,request,pk=None):
        monitor=self.get_object()
        checks=monitor.results.all()
        serializer= HealthCheckResultSerializer(checks, many=True)
        return Response(serializer.data)

    @decorators.action(detail=True,methods=['post'])
    def check_now(self,request,pk=None):
        monitor=self.get_object()
        if not monitor.is_active:
            return Response({'detail':'Monitor is inactive'},status=status.HTTP_400_BAD_REQUEST)
        
        check_url_health.delay(monitor.id)
        return Response({'detail':f'Health Check queued for {monitor.name}',
                         'task_id':task.id,
                         "monitor_id":monitor.id},status=status.HTTP_202_ACCEPTED)
    
   




































