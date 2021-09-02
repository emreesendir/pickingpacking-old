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

@csrf_exempt
@authorization('Manage | Sizing')
@api_view(['GET', 'POST'])
def sizing(request):
    if request.method == 'GET':
        orders = Order.objects.filter(status='WAITING FOR SIZING')
        res = list()
        for order in orders:
            res.append({
                        'id' : order.id,
                        'remoteId': order.remoteId,
                        'productLines': json.loads(order.productLines),
                        'status': order.status,
                        'commands': order.commands })
        return Response(res)

    elif request.method == 'POST':

        # execute each new size
        res = list()
        createdEvents = list()
        user = Token.objects.filter(key=request.headers['Authorization'].split()[1])[0].user.username
        for orderId, size in request.data.items():
            # bring order
            order = Order.objects.filter(id=int(orderId))[0]

            # check if event exist
            event = Event.objects.filter(cacheId=order.cacheId).filter(endpoint_id=order.endpoint_id).filter(type='ManagementSizing').exclude(result__startswith='ERROR')

            # if (there is no same open event & order has no size value & order status is waiting for sizing) : create new event
            if event.count() < 1:
                if order.status == 'WAITING FOR SIZING':
                    if order.size == '-' or order.size == '':
                        # create event
                        newEvent = Event(endpoint_id=order.endpoint_id, cacheId=order.cacheId, priority=4, time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), type='ManagementSizing', data=json.dumps({'size': size, 'user': user}), result='')
                        newEvent.save()
                        createdEvents.append({'eventId': newEvent.id, 'id': order.id, 'remoteId': order.remoteId})
                    else:
                        res.append({'id': order.id, 'remoteId': order.remoteId, 'result': 'Order has already had a size value: {}'.format(order.size)})
                else:
                    res.append({'id': order.id, 'remoteId': order.remoteId, 'result': 'Invalid order status: {}'.format(order.status)})
            else:
                res.append({'id': order.id, 'remoteId': order.remoteId, 'result': 'Event already exist!'})

        # wait for event results
        for dict in createdEvents:
            start = time.perf_counter()
            while True:
                event = Event.objects.get(id=dict['eventId'])
                if event.result == 'OK':
                    res.append({'id': dict['id'], 'remoteId': dict['remoteId'], 'result': 'OK'})
                    break
                elif event.result.startswith('ERROR'):
                    res.append({'id': dict['id'], 'remoteId': dict['remoteId'], 'result': event.result})
                    break
                elif time.perf_counter() - start > 10:
                    res.append({'id': dict['id'], 'remoteId': dict['remoteId'], 'result': 'Timeout'})
                    break
                time.sleep(0.4)

        return Response(res)

@csrf_exempt
@authorization('Manage | On Hold')
@api_view(['GET', 'POST'])
def onhold(request):
    if request.method == 'GET':
        orders = Order.objects.filter(Q(status='ON HOLD') | Q(status='ON HOLD FOR MERGE'))
        res = list()
        for order in orders:
            reason = str()
            if order.cacheId == -1:
                history = History.objects.filter(endpoint_id=order.endpoint_id).filter(remoteId=order.remoteId).filter(Q(status='ON HOLD') | Q(status='ON HOLD FOR MERGE')).order_by('-time')
            else:
                history = History.objects.filter(endpoint_id=order.endpoint_id).filter(cacheId=order.cacheId).filter(Q(status='ON HOLD') | Q(status='ON HOLD FOR MERGE')).order_by('-time')
            reason = history[0].event
            res.append({
                        'id' : order.id,
                        'remoteId': order.remoteId,
                        'productLines': json.loads(order.productLines),
                        'status': order.status,
                        'commands': order.commands,
                        'reason': reason })
        return Response(res)

    elif request.method == 'POST':

        # execute each new size
        res = list()
        createdEvents = list()
        user = Token.objects.filter(key=request.headers['Authorization'].split()[1])[0].user.username
        for orderId, size in request.data.items():
            # bring order
            order = Order.objects.filter(id=int(orderId))[0]

            # check if event exist
            if order.cacheId == -1:
                event = Event.objects.filter(endpoint_id=order.endpoint_id).filter(cacheId=order.cacheId).filter(data=json.dumps({'remoteId' : order.remoteId})).filter(type='OrderContinue').filter(result='')
            else:
                event = Event.objects.filter(endpoint_id=order.endpoint_id).filter(cacheId=order.cacheId).filter(type='OrderContinue').filter(result='')

            # if (there is no same open event & order has no size value & order status is waiting for sizing) : create new event
            if event.count() < 1:
                if order.status == 'ON HOLD' or order.status == 'ON HOLD FOR MERGE':
                    # create event
                    newEvent = Event(endpoint_id=order.endpoint_id, cacheId=order.cacheId, priority=4, time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), type='OrderContinue', data=json.dumps({'remoteId' : order.remoteId}), result='')
                    newEvent.save()
                    createdEvents.append({'eventId': newEvent.id, 'id': order.id, 'remoteId': order.remoteId})
                else:
                    res.append({'id': order.id, 'remoteId': order.remoteId, 'result': 'Invalid order status: {}'.format(order.status)})
            else:
                res.append({'id': order.id, 'remoteId': order.remoteId, 'result': 'Event already exist!'})

        # wait for event results
        for dict in createdEvents:
            start = time.perf_counter()
            while True:
                event = Event.objects.get(id=dict['eventId'])
                if event.result == 'OK':
                    res.append({'id': dict['id'], 'remoteId': dict['remoteId'], 'result': 'OK'})
                    break
                elif event.result.startswith('ERROR'):
                    res.append({'id': dict['id'], 'remoteId': dict['remoteId'], 'result': event.result})
                    break
                elif time.perf_counter() - start > 10:
                    res.append({'id': dict['id'], 'remoteId': dict['remoteId'], 'result': 'Timeout'})
                    break
                time.sleep(0.4)

        return Response(res)

@csrf_exempt
@authorization('Manage | In Progress')
@api_view(['GET'])
def inprogress(request):
    orders = Order.objects.exclude(status__in=['CANCELED', 'MARKED', 'SHIPPED'])
    res = list()
    for order in orders:
        res.append({
                    'id' : order.id,
                    'remoteId': order.remoteId,
                    'productLines': json.loads(order.productLines),
                    'status': order.status,
                    'commands': order.commands })
    return Response(res)

@csrf_exempt
@authorization('Manage | Archive')
@api_view(['GET'])
def archive(request):
    if request.method == 'GET':
        orders = Order.objects.filter(status__in=['CANCELED', 'MARKED', 'SHIPPED'])
        res = list()
        for order in orders:
            res.append({
                        'id' : order.id,
                        'remoteId': order.remoteId,
                        'productLines': json.loads(order.productLines),
                        'status': order.status,
                        'commands': order.commands })
        return Response(res)

@csrf_exempt
@authorization('Manage | Detail')
@api_view(['GET'])
def detail(request, orderId):
    order = Order.objects.get(pk=orderId)
    historyList = list()
    if order.cacheId == -1:
        historyQS = History.objects.filter(endpoint_id=order.endpoint_id).filter(remoteId=order.remoteId).order_by('-time')
    else:
        historyQS = History.objects.filter(endpoint_id=order.endpoint_id).filter(cacheId=order.cacheId).order_by('-time')
    for history in historyQS:
        historyList.append({
            'id' : history.id,
            'time' : history.time,
            'event' : history.event,
            'status' : history.status })
    res = {
            'id' : order.id,
            'source' : Dataflow.objects.get(pk=order.endpoint_id).name,
            'cacheId' : order.cacheId,
            'remoteId': order.remoteId,
            'productLines': json.loads(order.productLines),
            'shippingInformation' : json.loads(order.shippingInformation),
            'invoice' : order.invoice,
            'status': order.status,
            'size' : order.size,
            'commands': order.commands,
            'history': historyList }
    return Response(res)

@csrf_exempt
@authorization('Manage | Users')
@api_view(['POST', 'GET', 'PATCH'])
def users(request):
    if request.method == 'POST':
        if (request.data['password1'] == request.data['password2']):
            newuser = User.objects.create_user(request.data['username'], '', request.data['password1'])
            userp = UserPermission(user=newuser)
            userp.save()
            return Response({'result': 'OK'})
        else:
            response = JsonResponse({'Error': 'Passwords does not match!'})
            response.status_code = HTTPStatus.BAD_REQUEST
            return response
    
    elif request.method == 'GET':
        usersQS = User.objects.all().exclude(username='emreesendir')
        res = list()
        for user in usersQS:
            res.append({
                'id' : user.id,
                'username' : user.username,
            })
        return Response(res)

    elif request.method == 'PATCH':
        user = User.objects.get(pk=request.data['id'])
        userp = UserPermission.objects.get(user=user.id)
        oldPermissions = [qs.permission for qs in user.userpermission.permissions.all()]
        newPermissions = request.data['permissions']
        removedPermissions = list()
        for pr in oldPermissions:
            if (pr in newPermissions) : newPermissions.remove(pr)
            else: removedPermissions.append(pr)
        for pr in newPermissions:
            per = Permission.objects.get(permission=pr)
            userp.permissions.add(per.id)
        for pr in removedPermissions:
            per = Permission.objects.get(permission=pr)
            userp.permissions.remove(per.id)
        userp.save()
        return Response({'result': 'OK'})

@csrf_exempt
@authorization('Manage | Users')
@api_view(['GET', 'DELETE'])
def usersId(request, userId):
    if request.method == 'GET':
        if userId != 1:
            user = User.objects.get(pk=userId)
            return Response({
                    'id' : user.id,
                    'username' : user.username,
                    'allpermissions' : [permission.permission for permission in Permission.objects.all()],
                    'userpermissions' : [qs.permission for qs in user.userpermission.permissions.all()]
                })
        else:
            response = JsonResponse({'Error': 'Access denied!'})
            response.status_code = HTTPStatus.UNAUTHORIZED
            return response
    elif request.method == 'DELETE':
        user = User.objects.get(pk=userId)
        user.delete()
        return Response({'result': 'OK'})
