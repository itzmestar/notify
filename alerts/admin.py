from django.contrib import admin
from .models import NotificationType
from .models import Vehicle
from .models import SubscribeNotification
from .models import SentHistory

# Register your models here.




'''
class SubscribeNotificationAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['vehicle']}),
        ('Notifications', {'fields': ['notifyType'], 'classes': ['expand']}),
    ]

admin.site.register(SubscribeNotification, SubscribeNotificationAdmin)
'''
class SubscribeNotificationInline(admin.TabularInline):
    model = SubscribeNotification

class VehicleAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name']}),
        ('Details', {'fields': ['icon', 'imei', 'owner'], 'classes': ['collapse']}),
    ]
    list_display = ('name', 'imei', 'owner')
    inlines = [SubscribeNotificationInline]

admin.site.register(Vehicle, VehicleAdmin)

class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ('type', 'message')

admin.site.register(NotificationType, NotificationTypeAdmin)

class SentHistoryAdmin(admin.ModelAdmin):
    list_display = ('date_created', 'sent_to', 'notifyType', 'status', 'vehicle_address')

admin.site.register(SentHistory, SentHistoryAdmin)