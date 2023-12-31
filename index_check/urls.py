from django.urls import path
from .views import url_check_view, task_status, download_csv, fetch_url_status, reset_view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', url_check_view, name='check-urls'),
    path('task-status/', task_status, name='task_status'),
    path('download-csv/', download_csv, name='download_csv'),
    path('fetch-url-status/', fetch_url_status, name='fetch_url_status'),
    path('reset/', reset_view, name='reset_view'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)