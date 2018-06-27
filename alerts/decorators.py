import json
from functools import wraps
from django.conf import settings
from django.http import HttpRequest, HttpResponse

def dummy_json(view_func):

    @wraps(view_func)
    def wrapper_view_func(request, *args, **kwargs):

        if not request:
            return view_func(request, *args, **kwargs)

        # Add simple validation or your own validation rule
        if request.method == 'GET':
            request.json = None
        return view_func(request, *args, **kwargs)
        if request.content_type == 'application/json':
            if request.body:
                # Decode data to a dict object
                request.json = json.loads(request.body)
            else:
                request.json = None
        return view_func(request, *args, **kwargs)
    return wrapper_view_func