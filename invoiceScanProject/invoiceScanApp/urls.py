from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('save_edited_text/', views.save_edited_text, name='save_edited_text'),
    path('export/', views.export_data, name='export_data'),
]
