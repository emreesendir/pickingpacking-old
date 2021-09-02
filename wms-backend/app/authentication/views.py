from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Token


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def accessrights(request):
    token = Token.objects.filter(key=request.headers['Authorization'].split()[1])[0]
    permissions = [qs.permission for qs in token.user.userpermission.permissions.all()]
    return Response(permissions)
