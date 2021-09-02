from django.urls import path
from .views import pickcart, listpicking

urlpatterns = [
    path('pickcart/<str:pickcartBarcode>/', pickcart, name='picking-pickcart'),
    path('listpicking/', listpicking, name='picking-listpicking'),
]