from django.http.response import JsonResponse
from http import HTTPStatus
from .models import Token

def authorization(requiredPermission):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            try:
                token = Token.objects.filter(key=request.headers['Authorization'].split()[1])[0]
                permissions = [qs.permission for qs in token.user.userpermission.permissions.all()]
                if requiredPermission not in permissions:
                    raise Exception
            except:
                response = JsonResponse({'Error': 'Access denied!'})
                response.status_code = HTTPStatus.UNAUTHORIZED
                return response
            else:
                return view_func(request, *args, **kwargs)
        return wrapper_func
    return decorator