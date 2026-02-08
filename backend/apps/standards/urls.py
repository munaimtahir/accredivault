from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ControlViewSet, health_check

router = DefaultRouter()
router.register(r'controls', ControlViewSet, basename='control')

urlpatterns = [
    path('health', health_check, name='health-check'),
    path('', include(router.urls)),
]
