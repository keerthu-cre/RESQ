from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'status', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6, required=False)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'role', 'phone'
        ]
        extra_kwargs = {
            'email': {'required': False},
            'role': {'required': False},
        }

    def validate(self, attrs):
        confirm = attrs.pop('confirm_password', None)
        if confirm and attrs.get('password') != confirm:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.get('role', 'user')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.role = role
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Custom claims in JWT payload
        token['username'] = user.username
        token['role'] = user.role
        token['email'] = user.email
        token['status'] = user.status
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Verify user is active
        if self.user.status == 'blocked':
            raise serializers.ValidationError({"detail": "This account is blocked. Contact campus security admin."})
        
        # Include user profile data in login response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'phone': self.user.phone,
            'status': self.user.status,
        }
        
        # Include response team details if user is a responder
        if hasattr(self.user, 'response_team'):
            team = self.user.response_team
            data['team'] = {
                'id': team.id,
                'name': team.name,
                'zone': team.zone,
                'incident_types': team.incident_types,
                'availability_status': team.availability_status,
                'cases_handled': team.cases_handled,
                'avg_response_time': team.avg_response_time,
            }
        return data
