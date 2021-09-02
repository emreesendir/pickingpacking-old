from picking.models import PickingSession
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.deletion import SET_NULL

class Dataflow(models.Model):
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    command = models.CharField(max_length=50)
    lastupdate = models.CharField(max_length=50)
    cycleTime = models.IntegerField()

    def __str__(self):
        return self.name

class Order(models.Model):
    endpoint_id = models.IntegerField()
    cacheId = models.IntegerField()
    remoteId = models.CharField(max_length=50)
    productLines = models.CharField(max_length=1000)
    shippingInformation = models.CharField(max_length=500)
    invoice = models.CharField(max_length=500)
    status = models.CharField(max_length=50)
    size = models.CharField(max_length=50, default='')
    commands = models.CharField(max_length=300, default='')
    pickingSession = models.ForeignKey(PickingSession, on_delete=SET_NULL, null=True)
    
    class Meta:
        constraints = [UniqueConstraint(fields=['endpoint_id', 'cacheId', 'remoteId'], name='order-unique-constraint')]

class History(models.Model):
    endpoint_id = models.IntegerField()
    cacheId = models.IntegerField()
    remoteId = models.CharField(max_length=50, default='')
    time = models.CharField(max_length=50)
    event = models.CharField(max_length=300)
    status = models.CharField(max_length=50)

class Event(models.Model):
    endpoint_id = models.IntegerField()
    cacheId = models.IntegerField()
    priority = models.IntegerField()
    time = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    data = models.CharField(max_length=1500)
    result = models.CharField(max_length=300, default='')

class Odoo12_staging(models.Model):
    saleOrder = models.CharField(max_length=4000)
    stockPicking = models.CharField(max_length=4000)
    stockMove = models.CharField(max_length=4000)
    productProduct = models.CharField(max_length=4000)
    resPartner = models.CharField(max_length=4000)
    accountInvoice = models.CharField(max_length=4000)
    summary = models.CharField(max_length=4000)