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
    business_country = serializers.CharField(required=False, allow_blank=True)
    
    # Extra profile fields
    phone = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "password", "first_name", "last_name",
            "is_seller", "business_name", "business_description", 
            "business_address", "business_city", "business_postal_code", "business_country",
            "phone", "address", "city", "postal_code"
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
        business_country = validated_data.pop("business_country", "")
        
        phone = validated_data.pop("phone", "")
        address = validated_data.pop("address", "")
        city = validated_data.pop("city", "")
        postal_code = validated_data.pop("postal_code", "")
        
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
                profile.business_country = business_country
            
            if phone: profile.phone = phone
            if address: profile.address = address
            if city: profile.city = city
            if postal_code: profile.postal_code = postal_code
                
            profile.save()
            
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "phone", "address", "city", "postal_code",
            "is_seller", "business_name", "business_description", 
            "business_address", "business_city", "business_postal_code", "business_country",
            "min_order_amount", "delivery_time", "terms_of_sale",
            "mon_open", "mon_close", "sat_open", "sat_close", "sun_open", "sun_close",
            "seller_rating"
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    is_seller = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "profile", "is_seller"]

    def get_is_seller(self, obj):
        try:
            return obj.profile.is_seller
        except Exception:
            return False


class SellerSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='profile.business_name', read_only=True)
    description = serializers.CharField(source='profile.business_description', read_only=True)
    rating = serializers.FloatField(source='profile.seller_rating', read_only=True)
    city = serializers.CharField(source='profile.business_city', read_only=True)
    country = serializers.CharField(source='profile.business_country', read_only=True)
    products_count = serializers.SerializerMethodField()

    min_order_amount = serializers.DecimalField(source='profile.min_order_amount', read_only=True, max_digits=10, decimal_places=2)
    delivery_time = serializers.CharField(source='profile.delivery_time', read_only=True)
    terms_of_sale = serializers.CharField(source='profile.terms_of_sale', read_only=True)
    mon_open = serializers.TimeField(source='profile.mon_open', read_only=True)
    mon_close = serializers.TimeField(source='profile.mon_close', read_only=True)
    sat_open = serializers.TimeField(source='profile.sat_open', read_only=True)
    sat_close = serializers.TimeField(source='profile.sat_close', read_only=True)
    sun_open = serializers.TimeField(source='profile.sun_open', read_only=True)
    sun_close = serializers.TimeField(source='profile.sun_close', read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", 
            "business_name", "description", "rating", "city", "country", "products_count",
            "min_order_amount", "delivery_time", "terms_of_sale",
            "mon_open", "mon_close", "sat_open", "sat_close", "sun_open", "sun_close"
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
    # Upgrade to seller
    is_seller = serializers.BooleanField(required=False)
    # Shop settings
    business_name = serializers.CharField(required=False, allow_blank=True)
    business_description = serializers.CharField(required=False, allow_blank=True)
    business_address = serializers.CharField(required=False, allow_blank=True)
    business_city = serializers.CharField(required=False, allow_blank=True)
    business_postal_code = serializers.CharField(required=False, allow_blank=True)
    business_country = serializers.CharField(required=False, allow_blank=True)
    min_order_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    delivery_time = serializers.CharField(required=False, allow_blank=True)
    terms_of_sale = serializers.CharField(required=False, allow_blank=True)
    mon_open = serializers.TimeField(required=False, allow_null=True)
    mon_close = serializers.TimeField(required=False, allow_null=True)
    sat_open = serializers.TimeField(required=False, allow_null=True)
    sat_close = serializers.TimeField(required=False, allow_null=True)
    sun_open = serializers.TimeField(required=False, allow_null=True)
    sun_close = serializers.TimeField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "email", "phone", "address", "city", "postal_code",
            "is_seller", "business_name", "business_description", "business_address", "business_city", "business_postal_code", "business_country",
            "min_order_amount", "delivery_time", "terms_of_sale",
            "mon_open", "mon_close", "sat_open", "sat_close", "sun_open", "sun_close"
        ]

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
        profile_fields = {
            field: validated_data.pop(field, None) 
            for field in [
                "is_seller", "phone", "address", "city", "postal_code",
                "business_name", "business_description", "business_address", "business_city", "business_postal_code", "business_country",
                "min_order_amount", "delivery_time", "terms_of_sale",
                "mon_open", "mon_close", "sat_open", "sat_close", "sun_open", "sun_close"
            ]
        }
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
