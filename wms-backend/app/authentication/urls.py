from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import accessrights

urlpatterns = [
    path('token/', obtain_auth_token, name='authentication-login'),
    path('accessrights/', accessrights, name='authentication-accessrights')
]