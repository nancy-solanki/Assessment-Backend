import time
import logging

logger = logging.getLogger("django")


class RequestLoggingMiddleware:
    """
    Middleware to log every incoming HTTP request.
    Outputs: [METHOD] [PATH] [STATUS_CODE] [DURATION]ms (e.g. GET /api/meals 200 21ms)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        # Calculate elapsed duration in milliseconds
        duration_ms = int((time.time() - start_time) * 1000)

        log_message = f"{request.method} {request.path} {response.status_code} {duration_ms}ms"

        # Print directly to console stdout (perfect for local runserver and assessment logs)
        print(log_message)
        # Log using Django logger
        logger.info(log_message)

        return response
