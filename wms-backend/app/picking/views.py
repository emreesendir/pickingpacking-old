from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.contrib.auth.models import User
from django.http.response import JsonResponse
from http import HTTPStatus
from rest_framework.response import Response
from rest_framework.decorators import api_view
import json, datetime, time
from authentication.models import Permission, UserPermission
from dataflow.models import Order, Event, History, Dataflow
from authentication.decorators import authorization
from authentication.models import Token
from .models import PickCart, PickingSession


@csrf_exempt
@authorization('Manage | Sizing')
@api_view(['GET'])
def pickcart(request, pickcartBarcode):
    pickcart = PickCart.objects.get(barcode=pickcartBarcode)
    pickingsession = PickingSession.objects.filter(pickcart=pickcart.id).filter(status='PICKING IN PROGRESS')
    if pickingsession.count() > 0 : activePickingSession = pickingsession[0].id
    else : activePickingSession = False
    return Response({
                    'id' : pickcart.id,
                    'name' : pickcart.name,
                    'barcode' : pickcart.barcode,
                    'status' : pickcart.status,
                    'activePickingSession' : activePickingSession })

@csrf_exempt
@authorization('Manage | Sizing')
@api_view(['GET'])
def listpicking(request):
    orders = Order.objects.filter(status='WAITING FOR PICKING')
    res = list()
    for order in orders:
        res.append({
                    'id' : order.id,
                    'remoteId': order.remoteId,
                    'productLines': json.loads(order.productLines),
                    'status': order.status,
                    'commands': order.commands })
    return Response(res)