from django.db import models
from django.db.models.deletion import CASCADE, DO_NOTHING

class PickCart(models.Model):
    name = models.CharField(max_length=50)
    barcode = models.CharField(max_length=25)
    status = models.CharField(max_length=25, default='AVAILABLE')

    def __str__(self):
        return self.name

class PickCartSection(models.Model):
    pickcart = models.ForeignKey(PickCart, on_delete=CASCADE)
    number = models.IntegerField()
    barcode = models.CharField(max_length=25)
    size = models.CharField(max_length=25)

    def __str__(self):
        return '{} - {}'.format(self.pickcart.name, self.number)

class PickingSession(models.Model):
    timeStamp = models.DateTimeField(auto_now_add=True)
    totalSteps = models.IntegerField()
    currentStep = models.IntegerField()
    status = models.CharField(max_length=25)
    pickcart = models.ForeignKey(PickCart, on_delete=CASCADE)

class PickingStep(models.Model):
    pickingSession = models.ForeignKey(PickingSession, on_delete=CASCADE)
    stepNo = models.IntegerField()
    pickingLocation = models.IntegerField()
    pickCartSection = models.IntegerField()
    productName = models.CharField(max_length=100)
    totalQuantity = models.FloatField()
    pickedQuantity = models.FloatField()
    status = models.CharField(max_length=50)