from rest_framework.exceptions import APIException


class ExecutionUnavailable(APIException):
    status_code = 503
    default_detail = "The isolated execution service is not configured."
    default_code = "execution_unavailable"


class ProjectLimitExceeded(APIException):
    status_code = 403
    default_detail = "Free plan allows up to 3 active coding projects. Delete a project or upgrade your plan to create another."
    default_code = "coding_project_limit_exceeded"
