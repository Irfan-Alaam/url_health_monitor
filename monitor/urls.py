from rest_framework import routers
from .views import URLMonitorViewSet

router=routers.DefaultRouter()
router.register(r'monitors',URLMonitorViewSet,basename='monitor')

urlpatterns = router.urls
