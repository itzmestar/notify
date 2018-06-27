from django.shortcuts import render
from fcm_django.models import FCMDevice
from django.http import HttpResponse, JsonResponse
from .models import Vehicle, SubscribeNotification, SentHistory, NotificationType
import logging, json
import requests
import datetime
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger('alerts.views')

# response dict
RESPONSE = dict()
RESPONSE['data'] = {}
RESPONSE['error'] = []
RESPONSE['request'] = {}
RESPONSE['status'] = 'success'
RESPONSE['status_code'] = 200

ERROR_RESPONSE = RESPONSE.copy()
ERROR_RESPONSE['status'] = 'Forbidden'
ERROR_RESPONSE['status_code'] = 403

FORBIDDEN_RESPONSE = RESPONSE.copy()
FORBIDDEN_RESPONSE['status'] = 'Forbidden'
FORBIDDEN_RESPONSE['status_code'] = 403

ALERT_LIST_RESPONSE = RESPONSE.copy()
ALERT_LIST_RESPONSE['data']['total_records'] = 0
ALERT_LIST_RESPONSE['data']['records'] = []


AUTHENTICATION_URL = "http://127.0.0.1/apis2/check-token/"
VEHICLE_LIST_URL = "http://127.0.0.1/apis2/device-list/"


# Create your views here.

#inserting the fcm token into database, after receiving it from App
@csrf_exempt
def fcm_insert(request):
    if request.method == 'GET':
        return JsonResponse(FORBIDDEN_RESPONSE)

    json_data = get_json_body(request)

    if not json_data:
        ERROR_RESPONSE['status_code'] = 203
        ERROR_RESPONSE['status'] = 'param-missing'
        return JsonResponse(ERROR_RESPONSE)

    if "token" not in json_data \
        or "user" not in json_data \
        or "imei" not in json_data \
        or "fcm_token" not in json_data \
        or "type" not in json_data:
        ERROR_RESPONSE['status_code'] = 203
        ERROR_RESPONSE['status'] = 'param-missing'
        return JsonResponse(ERROR_RESPONSE)

    access_token = json_data["token"]
    user = json_data["user"]
    imei = json_data["imei"]
    fcm_token = json_data["fcm_token"]
    device_type = json_data["type"]

    logger.debug(access_token + ',' + user +','+imei+','+fcm_token+','+device_type)

    if access_token == "" \
        or access_token == "" \
        or user == "" \
        or imei == "" \
        or fcm_token == "":
        ERROR_RESPONSE['status_code'] = 203
        ERROR_RESPONSE['status'] = 'param-value-error'
        return JsonResponse(ERROR_RESPONSE)

    # check authentication
    if is_authenticated(access_token) == False:
        return JsonResponse(FORBIDDEN_RESPONSE)

    # lookup if already exists in db
    try:
        dev = FCMDevice.objects.get(device_id=imei, name=user)
    except FCMDevice.DoesNotExist:
        # if not present then add to db
        dev = FCMDevice(registration_id=fcm_token, name=user, device_id=imei, type=device_type)
        dev.save()
    else:
        # if already present then update its attributes
        dev.registration_id = fcm_token
        dev.save()

    # dev.send_message(title="Register", body="django Register ok", data={"test": "test"})

    # fetch the vehicle list & update db with it
    fetch_vehicle_list(dev, access_token)
    return JsonResponse(RESPONSE)

# api call to send notification for an event
@csrf_exempt
def send_notification(request):
    if request.method == 'GET':
        #do_something()
        logger.error("send_notification: called with GET")
        return JsonResponse(FORBIDDEN_RESPONSE)

    json_data = get_json_body(request)

    if not json_data:
        ERROR_RESPONSE['status_code'] = 203
        ERROR_RESPONSE['status'] = 'param-missing'
        logger.error("send_notification: json data None")
        return JsonResponse(ERROR_RESPONSE)

    if "token" not in json_data \
        or "type" not in json_data \
        or "address" not in json_data \
        or "imei" not in json_data:
        ERROR_RESPONSE['status_code'] = 203
        ERROR_RESPONSE['status'] = 'param-missing'
        logger.error("send_notification: param missing")
        return JsonResponse(ERROR_RESPONSE)

    access_token = json_data["token"]
    notify_type = json_data["type"]
    imei = json_data["imei"]
    address = json_data["address"]

    #authenticate by key
    if access_token != 'y^*0h4rv2z(!)ty@-m3cn(%n#o_z3nk@x5c!2d-gj!7)b$&(':
        logger.error("send_notification: wrong token")
        return JsonResponse(FORBIDDEN_RESPONSE)

    logger.debug("send_notification: authenticated."+imei+', '+notify_type+', '+address)
    # find out the vehicle details from imei
    try:
        vehicle_owner_list = Vehicle.objects.filter(imei=imei)
    except:
        # no such vehicle in db -> do nothing
        logger.error("send_notification: exception in db")
        return JsonResponse(FORBIDDEN_RESPONSE)
    else:
        # if empty list then return
        if len(vehicle_owner_list) == 0:
            logger.error("send_notification: no such vehicle in db")
            return JsonResponse(FORBIDDEN_RESPONSE)

    # found the vehicle list

    # check subscription to this notification type

    try:
        notifyType = NotificationType.objects.get(type=notify_type)
    except NotificationType.DoesNotExist:
        # no subscription for this type of alert then do nothing
        logger.error("send_notification: no such notify type in db")
        return JsonResponse(RESPONSE)

    try:
        notify_sub = SubscribeNotification.objects.get(vehicle=vehicle_owner_list[0], notifyType=notifyType)
    except SubscribeNotification.DoesNotExist:
        # no subscription for this type of alert then do nothing
        logger.error("send_notification: no subscription for this vehicle-notify type in db")
        return JsonResponse(RESPONSE)

    #send the notification

    for vehicle in vehicle_owner_list:
        fcm_device = vehicle.owner
        try:
            d = datetime.datetime.now()
            ts = d.strftime('%d-%m-%Y %H:%M:%S')
            fcm_device.send_message(title=vehicle.name, body=notify_type, data={"datetime": ts, "address": address, "imei": vehicle.imei})
        except:
            status = "F"
            logger.debug("send_notification: notification sending failed.")
        else:
            status = "S"
            logger.debug("send_notification: notification sent successfully.")

        sent_history = SentHistory(date_created=d, notifyType=notify_sub, sent_to=fcm_device, status=status, vehicle_address=address)
        sent_history.save()

    return JsonResponse(RESPONSE)


# list the notifications
@csrf_exempt
def list_notification(request):
    if request.method == 'GET':
        return JsonResponse(FORBIDDEN_RESPONSE)

    json_data = get_json_body(request)

    if json_data is None:
        logger.debug("json_data is None")
        ERROR_RESPONSE['status_code'] = 203
        ERROR_RESPONSE['status'] = 'param-missing'
        return JsonResponse(ERROR_RESPONSE)

    if "token" not in json_data \
        or "imei" not in json_data \
        or "user" not in json_data \
        or "filter" not in json_data:
        logger.debug("Missing a param")
        ERROR_RESPONSE['status_code'] = 203
        ERROR_RESPONSE['status'] = 'param-missing'
        return JsonResponse(ERROR_RESPONSE)

    access_token = json_data["token"]
    imei = json_data["imei"]
    user = json_data["user"]
    filter = json_data["filter"]

    logger.debug(access_token + ',' +imei+','+user+','+filter)

    # check authentication
    if is_authenticated(access_token) is False:
       return JsonResponse(FORBIDDEN_RESPONSE)

    # lookup if user exists in db
    try:
        dev = FCMDevice.objects.get(device_id=imei, name=user)
    except FCMDevice.DoesNotExist:
        # dev not present. send an empty list
        logger.debug("dev not present in db. sending an empty list")
        return JsonResponse(ALERT_LIST_RESPONSE)

    diff = 1 #in case, no filter is present then send data for last 1 hr
    # if present then fetch alerts from db
    if type(filter) == int:
        diff = filter
    elif type(filter) == str:
        #try to find the hours
        try:
            diff = int(filter)
        except:
            diff = 1

    now = timezone.now()
    earlier_ts = now -  timedelta(hours=diff)

    notifications = SentHistory.objects.filter(sent_to=dev).filter(date_created__range=(earlier_ts, now))

    if len(notifications) == 0:
        logger.debug("0 notifications present in db. sending an empty list")
        return JsonResponse(ALERT_LIST_RESPONSE)

    ALERT_LIST_RESPONSE['data']['total_records'] = len(notifications)
    ALERT_LIST_RESPONSE['data']['msg'] = 'Notification List for last {} hours'.format(diff)
    ALERT_LIST_RESPONSE['data']['records'] = []
    for alert in notifications:
        notif = dict()
        notif['name'] = alert.notifyType.vehicle.name
        notif['imei'] = alert.notifyType.vehicle.imei
        notif['type'] = alert.notifyType.vehicle.icon
        notif['datetime'] = alert.date_created
        notif['alert_type'] = alert.notifyType.notifyType.type
        notif['details'] = alert.notifyType.notifyType.message
        notif['address'] = alert.vehicle_address
        ALERT_LIST_RESPONSE['data']['records'].append(notif)

    return JsonResponse(ALERT_LIST_RESPONSE)



# helping functions

# fetch velicle list for a given token & populate db with it
def fetch_vehicle_list(fcm_device, token):
    payload={
        "token": token,
        "filter_device_name": "",
        "sort_by": "name"
    }
    try:
        r = requests.post(VEHICLE_LIST_URL, json=payload, timeout=1)
        data = r.json()
        if data['status_code'] != 200:
            # error
            return

        owner = fcm_device

        for record in data['page']['records']:
            icon = record['icon']
            name = record['name']
            imei = record['imei']

            try:
                vehicle = Vehicle.objects.get(imei=imei, owner=owner)
            except Vehicle.DoesNotExist:
                # if not present then add to db
                vehicle = Vehicle(icon=icon, name=name, imei=imei, owner=owner)
                vehicle.save()
            else:
                # if already present then update its attributes
                pass

    except Exception:
        logger.error()
        return

# returns the json body from requests as dict if found else None
def get_json_body(request):
    if request.content_type == 'application/json':
        if request.body:
            # Decode data to a dict object
            return json.loads(request.body.decode('utf-8'))
        else:
            logger.debug('Body not found')
    else:
        logger.debug('Content type is not json')
    return None

# check authentication of a token
# returns True if authenticated; False otherwise
def is_authenticated(token):
    # check authentication
    try:
        payload = {'token': token}
        r = requests.post(AUTHENTICATION_URL, json=payload, timeout=1)
        data = r.json()
        if data['status_code'] != 200:
            return False
    except:
        return False
    else:
        return True