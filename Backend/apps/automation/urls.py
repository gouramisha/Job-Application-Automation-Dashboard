from rest_framework.routers import DefaultRouter

from .views import AutomationRunViewSet, SupportedSiteViewSet

router = DefaultRouter()
router.register("runs", AutomationRunViewSet, basename="automation-run")
router.register("sites", SupportedSiteViewSet, basename="automation-site")

urlpatterns = router.urls
