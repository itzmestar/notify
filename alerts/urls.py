from django.urls import path

from . import views

app_name = 'alerts'
urlpatterns = [
    #path('', views.IndexView.as_view(), name='index'),
    path(r'insert/', views.fcm_insert, name='insert'),
    path(r'notify/', views.send_notification, name='notify'),
    path(r'list/', views.list_notification, name='list'),
]
