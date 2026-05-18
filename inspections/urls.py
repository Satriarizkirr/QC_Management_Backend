from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InspectionViewSet, DefectDetailViewSet, DashboardStatsView,
    AssemblingInspectionViewSet, AssemblingDefectDetailViewSet
)

router = DefaultRouter()
router.register(r'inspections', InspectionViewSet)
router.register(r'defects', DefectDetailViewSet)
router.register(r'assembling-inspections', AssemblingInspectionViewSet)
router.register(r'assembling-defects', AssemblingDefectDetailViewSet)

urlpatterns = [
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('', include(router.urls)),
]
