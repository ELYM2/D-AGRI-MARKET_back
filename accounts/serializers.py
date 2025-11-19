from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UserProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        validate_password(password)
        email = validated_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "Email already in use"})
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["phone", "address", "city", "postal_code"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "profile"]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        current = attrs.get("current_password")
        new = attrs.get("new_password")
        if not user.check_password(current):
            raise serializers.ValidationError({"current_password": "Incorrect current password"})
        validate_password(new, user)
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "address", "city", "postal_code"]

    def validate_email(self, value):
        if not value:
            return value
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Email already in use")
        return value

    def update(self, instance, validated_data):
        profile_fields = {field: validated_data.pop(field, None) for field in ["phone", "address", "city", "postal_code"]}
        for attr, value in validated_data.items():
            if value is not None:
                setattr(instance, attr, value)
        instance.save()
        profile = getattr(instance, "profile", None)
        if not profile:
            profile = UserProfile.objects.create(user=instance)
        for attr, value in profile_fields.items():
            if value is not None:
                setattr(profile, attr, value)
        profile.save()
        return instance
