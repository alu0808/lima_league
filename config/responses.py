from rest_framework.response import Response
from rest_framework import status as http

def ok(data=None, message="OK", extra=None, status_code=http.HTTP_200_OK):
    payload = {"status": "success", "message": message}
    if data is not None:
        payload["data"] = data
    if extra:
        payload.update(extra)
    return Response(payload, status=status_code)

def created(data=None, message="Creado", extra=None):
    return ok(data=data, message=message, extra=extra, status_code=http.HTTP_201_CREATED)

def error(message="Error", errors=None, code=None, status_code=http.HTTP_400_BAD_REQUEST):
    payload = {"status": "error", "message": message}
    if code:
        payload["code"] = code
    if errors is not None:
        payload["errors"] = errors
    return Response(payload, status=status_code)