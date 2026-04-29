from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Quality Administration"
admin.site.site_title = "Quality Admin Portal"
admin.site.index_title = "Welcome to QC Tracker Portal"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('inspections.urls')),
]
