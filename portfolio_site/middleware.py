class PermissionsPolicyMiddleware:
    """
    Middleware to set the Permissions-Policy security header.
    Disables browser features not required by the site (camera, microphone, geolocation).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if "Permissions-Policy" not in response:
            response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response
