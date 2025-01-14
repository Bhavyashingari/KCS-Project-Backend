import jwt
from django.conf import settings
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken

class AzureADTokenValidationMiddleware:
    """
    Middleware to validate Azure AD JWT tokens for incoming requests.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the Authorization header from the request
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                # Validate and decode the token using Django's JWT tools or pyjwt
                AccessToken(token)  # Throws an error if invalid
                decoded_token = jwt.decode(
                    token,
                    options={"verify_signature": False},  # Decode without verification
                )

                # Attach user information to the request object (optional)
                request.user_data = {
                    "user_id": decoded_token.get("oid"),  # Object ID from Azure AD
                    "email": decoded_token.get("email"),
                    "name": decoded_token.get("name"),
                }
            except jwt.ExpiredSignatureError:
                return JsonResponse({"detail": "Token has expired"}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({"detail": "Invalid token"}, status=401)

        return self.get_response(request)
