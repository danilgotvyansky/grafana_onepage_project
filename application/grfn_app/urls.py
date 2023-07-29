from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_dashboard, name='main_dashboard'),
    path('get_embed_url/', views.get_embed_url, name='get_embed_url'),
]