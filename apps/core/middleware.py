class SecurityHeadersMiddleware:
    """
    Appends defense-in-depth HTTP security headers to all outgoing responses:
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: camera=(), microphone=()
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not response.has_header('Referrer-Policy'):
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        if not response.has_header('Permissions-Policy'):
            response['Permissions-Policy'] = 'camera=(), microphone=()'
        return response
