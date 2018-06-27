from django.db import models
from fcm_django.models import FCMDevice
# Create your models here.

#Types of Notifications such as: Ignition On, Ingnition Off etc
class NotificationType(models.Model):
    type = models.CharField(max_length=64, unique=True, verbose_name="Type")
    message = models.CharField(verbose_name="Message", max_length=64)

    def __str__(self):
        return "{}".format(self.type)

#Vehicle list it must be populated regularly
class Vehicle(models.Model):
    icon = models.CharField(max_length=20, verbose_name="Type")
    name = models.CharField(max_length=64, verbose_name="Name")
    imei = models.CharField(max_length=20, verbose_name="IMEI", db_index=True) #imei of the vehicle device
    owner = models.ForeignKey(FCMDevice, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('imei', 'owner'),)

    def __str__(self):
        return "{}".format(self.name)

#Notifications to be sent for which NotificationType for which Vehicles
class SubscribeNotification(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    notifyType = models.ForeignKey(NotificationType, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('vehicle', 'notifyType'),)

    def __str__(self):
        return "{} : {}".format(self.vehicle, self.notifyType)

#Notifications sent history
class SentHistory(models.Model):
    STATUS = (
        ('S', 'Success'),
        ('F', 'Failure')
    )
    date_created = models.DateTimeField(
        verbose_name=("Creation Time"),
        auto_now_add=True,
        null=False
    )

    notifyType = models.ForeignKey(
        SubscribeNotification,
        on_delete=models.CASCADE
    )

    sent_to = models.ForeignKey(FCMDevice, on_delete=models.CASCADE)

    status = models.CharField(max_length=1,
        choices=STATUS,
        default='F',
        verbose_name = ("Status"),
        )

    vehicle_address = models.CharField(max_length=500,
                                       verbose_name=("Vehicle Address"), blank=True)
    def __str__(self):
        return "{} : {} : {} : {}".format(self.date_created,  self.sent_to, self.notifyType, self.status)

