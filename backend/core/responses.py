from rest_framework.response import Response


def api_response(data=None, *, request=None, status=200, meta=None):
    payload = {"data": data, "request_id": getattr(request, "request_id", None)}
    if meta is not None:
        payload["meta"] = meta
    return Response(payload, status=status)

