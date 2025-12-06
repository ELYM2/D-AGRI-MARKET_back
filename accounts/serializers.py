from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UserProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    
    # Seller fields
    is_seller = serializers.BooleanField(required=False, default=False)
    business_name = serializers.CharField(required=False, allow_blank=True)
    business_description = serializers.CharField(required=False, allow_blank=True)
    business_address = serializers.CharField(required=False, allow_blank=True)
    business_city = serializers.CharField(required=False, allow_blank=True)
    business_postal_code = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "password", "first_name", "last_name",
            "is_seller", "business_name", "business_description", 
            "business_address", "business_city", "business_postal_code"
        ]

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        # Extract non-user fields
        is_seller = validated_data.pop("is_seller", False)
        business_name = validated_data.pop("business_name", "")
        business_description = validated_data.pop("business_description", "")
        business_address = validated_data.pop("business_address", "")
        business_city = validated_data.pop("business_city", "")
        business_postal_code = validated_data.pop("business_postal_code", "")
        
        password = validated_data.pop("password")
        
        # Validate password
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": e.messages})
        
        email = validated_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "Email already in use"})
            
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # Update profile
        if hasattr(user, 'profile'):
            profile = user.profile
            profile.is_seller = is_seller
            if is_seller:
                profile.business_name = business_name
                profile.business_description = business_description
                profile.business_address = business_address
                profile.business_city = business_city
                profile.business_postal_code = business_postal_code
            profile.save()
            
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "phone", "address", "city", "postal_code",
            "is_seller", "business_name", "business_description", "seller_rating"
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    is_seller = serializers.BooleanField(source='profile.is_seller', read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "profile", "is_seller"]


class SellerSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='profile.business_name', read_only=True)
    description = serializers.CharField(source='profile.business_description', read_only=True)
    rating = serializers.FloatField(source='profile.seller_rating', read_only=True)
    city = serializers.CharField(source='profile.business_city', read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", 
            "business_name", "description", "rating", "city", "products_count"
        ]

    def get_products_count(self, obj):
        return obj.products.count()


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
