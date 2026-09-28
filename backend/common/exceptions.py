from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        message = "An error occurred."
        errors = {}

        if isinstance(response.data, dict):
            if "detail" in response.data:
                message = str(response.data["detail"])
                errors = response.data
            else:
                message = "Validation failed."
                errors = response.data
        elif isinstance(response.data, list):
            message = "Validation failed."
            errors = {"non_field_errors": response.data}
        else:
            message = str(response.data)

        response.data = {
            "success": False,
            "message": message,
            "errors": errors,
        }

    return response
