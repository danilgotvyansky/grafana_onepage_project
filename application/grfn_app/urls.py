from .views import main_dashboard, disconnect_grafana,change_slide_interval
from django.urls import path

urlpatterns = [
    path('', main_dashboard, name='main_dashboard'),
    path('disconnect/', disconnect_grafana, name='disconnect_grafana'),
    path('change_slide_interval/', change_slide_interval, name='change_slide_interval'),
]