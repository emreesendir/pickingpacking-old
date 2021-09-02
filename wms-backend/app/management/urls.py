from django.urls import path
from .views import sizing, onhold, inprogress, archive, detail, users, usersId

urlpatterns = [
    path('sizing/', sizing, name='management-sizing'),
    path('onhold/', onhold, name='management-onhold'),
    path('inprogress/', inprogress, name='management-inprogress'),
    path('archive/', archive, name='management-archive'),
    path('detail/<int:orderId>/', detail, name='management-detail'),
    path('users/', users, name='management-users'),
    path('users/<int:userId>/', usersId, name='management-usersId'),
]