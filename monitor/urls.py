from django.urls import path,include    
from rest_framework import routers
from .views import URLMonitorViewSet

router=routers.DefaultRouter()
router.register(r'monitors',URLMonitorViewSet,basename='monitor')

urlpatterns = [
    path("", include(router.urls)),
]
# print("ROUTER URLS:", router.urls)