from django.urls import path

from . import views

urlpatterns = [
    path('',views.main, name='main'),
    path('upload/', views.upload, name='upload'), 
    path('modify/', views.modify, name='modify'),
    path('download/', views.download, name='download'),
    path('clear/', views.clear, name='clear')
]

