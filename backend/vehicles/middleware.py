from django.http import HttpResponseForbidden


class IPFilterMiddleware:
    """
    Simple IP filtering.
    For now, allows localhost (dev).
    """

    ALLOWED_IPS = [
        "127.0.0.1",
        "::1",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_client_ip(request)

        # For demo: log IP or restrict here
        if self.ALLOWED_IPS and ip not in self.ALLOWED_IPS:
            return HttpResponseForbidden("Access denied: IP not allowed")

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
