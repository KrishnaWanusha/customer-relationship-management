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

    if response is None:
        try:
            from botocore.exceptions import BotoCoreError, ClientError
            if isinstance(exc, (ClientError, BotoCoreError)):
                from rest_framework import status
                from rest_framework.response import Response
                return Response(
                    {
                        "success": False,
                        "message": "Storage service error occurred while processing the file.",
                        "errors": {"storage": [str(exc)]},
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except ImportError:
            pass

    return response
