from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    request = context.get("request")
    details = response.data
    message = "The request could not be completed."
    code = getattr(exc, "default_code", "request_error")
    if isinstance(details, dict) and "detail" in details:
        message = str(details["detail"])
        fields = {}
    else:
        fields = details if isinstance(details, dict) else {"non_field_errors": details}
    response.data = {
        "error": {"code": str(code), "message": message, "fields": fields},
        "request_id": getattr(request, "request_id", None),
    }
    return response

