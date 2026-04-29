import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inspections.views import DashboardStatsView
from django.test import RequestFactory

request = RequestFactory().get('/api/dashboard-stats/')
view = DashboardStatsView()
try:
    response = view.get(request)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
