from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InspectionViewSet, DefectDetailViewSet, DashboardStatsView

router = DefaultRouter()
router.register(r'inspections', InspectionViewSet)
router.register(r'defects', DefectDetailViewSet)

urlpatterns = [
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('', include(router.urls)),
]
