from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("review/", views.review, name="review"),
    path("save/", views.save_edited_text, name="save_edited_text"),
    path("export/", views.export_data, name="export_data"),
]
