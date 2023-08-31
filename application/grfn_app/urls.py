from .views import main_dashboard, disconnect_grafana
from django.urls import path

urlpatterns = [
    path('', main_dashboard, name='main_dashboard'),
    path('disconnect/', disconnect_grafana, name='disconnect_grafana'),
]