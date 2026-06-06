

from rest_framework import serializers
from .models import *  # Импортируйте модели

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer()  # Или используйте PrimaryKeyRelatedField или StringRelatedField

    class Meta:
        model = User
        fields = ['id', 'role', 'phone', 'password', 'isActive', 'dateJoined']

class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'name', 'description', 'icon', 'points']

class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer()
    class Meta:
        model = UserAchievement
        fields = ['achievement', 'dateEarned']

class SubscriptionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionCategory
        fields = ['id', 'name']


class SubscriptionSerializer(serializers.ModelSerializer):
    category = SubscriptionCategorySerializer()
    class Meta:
        model = Subscription
        fields = ['id', 'category', 'title', 'durationDays', 'price']

class MemberSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Member
        fields = ['id', 'user', 'image','firstName', 'lastName', 'patronymic', 'dateOfBirth', 'phone', 'email', 'passportData']
class VisitSerializer(serializers.ModelSerializer):
    member = MemberSerializer()
    class Meta:
        model = Visit
        fields = ['id', 'member', 'visitDate']

class AdminSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Administrator
        fields = ['id', 'user', 'image', 'firstName', 'lastName', 'patronymic', 'dateOfBirth', 'phone']


class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Notification
        fields = ['id', 'user', 'createdAt', 'title', 'text', 'isRead']

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'image', 'title', 'content', 'date']

class CoachTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachType
        fields = ['id', 'name']

class CoachSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    coachType = CoachTypeSerializer()
    class Meta:
        model = Coach
        fields = ['id', 'user','coachType', 'image', 'firstName', 'lastName', 'patronymic', 'passportData', 'phone', 'experience', 'dateOfBirth', 'email', 'price']

class ReviewSerializer(serializers.ModelSerializer):
    user = MemberSerializer()
    trainer = CoachSerializer()
    class Meta:
        model = Review
        fields = ['id', 'user', 'trainer', 'text', 'dateCreated']

class EducationSerializer(serializers.ModelSerializer):
    trainer = CoachSerializer()
    class Meta:
        model = Education
        fields = ['id', 'name', 'trainer']

class DirectionSerializer(serializers.ModelSerializer):
    trainer = CoachSerializer()
    class Meta:
        model = Direction
        fields = ['id', 'name', 'trainer']

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'title', 'description', 'image']

class PreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preview
        fields = ['id', 'title', 'description', 'image']

class ShopCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopCategory
        fields = ['id', 'title']

class ShopItemSerializer(serializers.ModelSerializer):
    # Для сериализации — вложенный сериализатор
    category = ShopCategorySerializer(read_only=True)
    # Для десериализации — только id
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ShopCategory.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = ShopItem
        fields = ['id', 'img', 'title', 'description', 'price', 'quantity', 'category', 'category_id']


class BasketSerializer(serializers.ModelSerializer):
    item = ShopItemSerializer()
    member = MemberSerializer()
    class Meta:
        model = Basket
        fields = ['id', 'item', 'member', 'quantity', 'price']

class GetPreviewTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GetPreviewTags
        fields = ['id', 'description', 'image']

class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = ['id', 'numberPhone']

class TimetableCoachSerializer(serializers.ModelSerializer):
    trainer = CoachSerializer()
    member = MemberSerializer()
    class Meta:
        model = TimetableCoach
        fields = ['id', 'trainer', 'member', 'typeTraining', 'dateTime', 'amount', 'status']

class TimetableCoachPaymentSerializer(serializers.ModelSerializer):
    timetableСoach = TimetableCoachSerializer()

    class Meta:
        model = TimetableCoachPayment
        fields = ['id', 'timetableСoach', 'paymentId', 'amount', 'currency', 'status', 'createdAt', 'updatedAt']

class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    class StatusSerializer(serializers.Serializer):
        # можно оставить просто как поле, или сделать вложенный сериализатор
        pass
    subscription = SubscriptionSerializer()
    class Meta:
        model = SubscriptionPayment
        fields = ['id', 'subscription', 'paymentID', 'amount', 'currency', 'status', 'createdAt', ]

class BuyItemSerializer(serializers.ModelSerializer):
    item = ShopItemSerializer()
    member = MemberSerializer()
    class Meta:
        model = BuyItem
        fields = ['id', 'item', 'member', 'date']

class ShopPaymentSerializer(serializers.ModelSerializer):
    item = ShopItemSerializer()
    class Meta:
        model = ShopPayment
        fields = ['id', 'item', 'paymentID', 'amount', 'currency', 'quantity', 'status', 'createdAt', ]

class BuySubscriptionSerializer(serializers.ModelSerializer):
    buySubscription = SubscriptionPaymentSerializer()
    personal_card = serializers.StringRelatedField()
    class Meta:
        model = BuySubscription
        fields = ['id', 'buySubscription', 'startDate', 'endDate', 'personalCard', 'isActive']






class CustomTokenObtainSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        phone = data.get('phone')
        password = data.get('password')
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден")
        if password != user.password:
            raise serializers.ValidationError("Пароль не верный")

        # Проверка роли (только для Администратора)
        if user.role is None or user.role.name != "Администратор":
            raise serializers.ValidationError("Доступ только для администраторов")

        user_serializer = UserSerializer(user)
        return {
            'user': user_serializer.data,
        }