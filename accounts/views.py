from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import RegisterSerializer, CustomUserSerializer, CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Registers a new student/user or responder.
    """
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens immediately upon registration
        refresh = RefreshToken.for_user(user)
        refresh['username'] = user.username
        refresh['role'] = user.role
        refresh['email'] = user.email

        return Response({
            "message": "User registered successfully.",
            "user": CustomUserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Returns JWT access + refresh tokens and user profile details.
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/auth/profile/
    Returns currently logged-in user profile.
    """
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
