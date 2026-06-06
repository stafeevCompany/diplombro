import random
import string

from django.utils import timezone
from django.db import models
from django.utils.translation import gettext_lazy as _

import qrcode
from io import BytesIO
from django.core.files.base import ContentFile


class Role(models.Model):
    name = models.CharField(max_length=50, default="Пользователь", unique=True)

    def __str__(self):
        return self.name


class User(models.Model):
    role = models.ForeignKey(Role,  on_delete=models.CASCADE, null=True, related_name='users')
    phone = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    isActive = models.BooleanField(default=False)
    dateJoined = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.phone



class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to='achievement_icons/', blank=True, null=True)
    points = models.IntegerField(default=10)  # Баллы за достижение

    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    dateEarned = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')  # Пользователь не может получить одно достижение дважды

class SubscriptionCategory(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    category = models.ForeignKey(SubscriptionCategory,  on_delete=models.CASCADE, null=True, related_name='category_subscriptions')
    title = models.CharField(max_length=50)
    durationDays = models.PositiveIntegerField()
    price = models.IntegerField()

    def __str__(self):
        return self.title


class Tag(models.Model):
    title = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.title


class TagImage(models.Model):
    image = models.ImageField(upload_to='media/images/tags/')

    def __str__(self):
        return f'TagImage {self.id}'


class TagImageRelation(models.Model):
    image = models.ForeignKey(TagImage, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(Tag,  on_delete=models.CASCADE, null=True, related_name='images')

    class Meta:
        unique_together = ('image', 'tag')


class SubscriptionFeature(models.Model):
    subscription = models.ForeignKey(Subscription,  on_delete=models.CASCADE, related_name='features')
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Member(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='member')
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50)
    dateOfBirth = models.DateField()
    phone = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    passportData = models.CharField(max_length=11)
    image = models.ImageField(upload_to='media/images/members/', default="media/images/members/free-icon-user-9684504.png")

    def __str__(self):
        return f" {self.lastName} {self.firstName} {self.patronymic}"

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Сохраняем изображение в BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    filename = 'qr_code.png'
    # Возвращаем файл
    return ContentFile(buffer.getvalue(), name=filename)

def generate_unique_code(length=8):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))

class PersonalCard(models.Model):
    code = models.CharField(max_length=50, unique=True, blank=True)
    qrCode = models.ImageField(upload_to='media/images/qr_codes/')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, related_name='cards')

    def save(self, *args, **kwargs):
        # Генерация уникального кода, если он не установлен
        if not self.code:
            while True:
                new_code = generate_unique_code()
                if not PersonalCard.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break

        # Генерация QR-кода, если его нет
        if not self.qrCode:
            qr_data = (
                f'{self.member.lastName} {self.member.firstName} {self.member.patronymic}\n'
                f'{self.member.phone}\n'
                f'{self.member.dateOfBirth}\n'
            )
            qr_image = generate_qr_code(qr_data)  # Ваша функция генерации QR-кода
            self.qrCode.save('qr_code.png', qr_image, save=False)

        super().save(*args, **kwargs)



class Visit(models.Model):
    member = models.ForeignKey(Member,  on_delete=models.CASCADE, null=True, related_name='visits')
    visitDate = models.DateTimeField(default=timezone.now)


class Notification(models.Model):
    user = models.ForeignKey(User,  on_delete=models.CASCADE, null=True, related_name='notifications')
    createdAt = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    text = models.TextField()
    isRead = models.BooleanField(default=False)

    def __str__(self):
        return self.title




class News(models.Model):
    image = models.ImageField(upload_to='media/images/news/')
    title = models.CharField(max_length=50)
    content = models.TextField()
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title


class CoachType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Coach(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='coach')
    image = models.ImageField(upload_to='media/images/coach/')
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50)
    passportData = models.CharField(max_length=11)
    phone = models.CharField(max_length=50, unique=True)
    experience = models.TextField()
    dateOfBirth = models.DateField()
    email = models.CharField()
    coachType = models.ForeignKey(CoachType, on_delete=models.SET_NULL, null=True, related_name='type')
    price = models.IntegerField()

    def __str__(self):
        return f" {self.lastName} {self.firstName} {self.patronymic}"

# Отзывы посетителей
class Review(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='reviews')
    trainer = models.ForeignKey(Coach, on_delete=models.CASCADE)
    text = models.TextField()
    dateCreated = models.DateTimeField(auto_now_add=True)



class Education(models.Model):
    name = models.CharField(max_length=100)
    trainer = models.ForeignKey(Coach,  on_delete=models.CASCADE, null=True, related_name='educations')

    def __str__(self):
        return self.name


class Direction(models.Model):
    name = models.CharField(max_length=100)
    trainer = models.ForeignKey(Coach,  on_delete=models.CASCADE, null=True, related_name='directions')

    def __str__(self):
        return self.name


class Administrator(models.Model):
    user = models.ForeignKey(User,  on_delete=models.CASCADE, related_name='administrator')
    image = models.ImageField(upload_to='media/images/coach/')
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50)
    passport_data = models.CharField(max_length=11)
    phone = models.CharField(max_length=50, unique=True)
    email = models.CharField()
    dateOfBirth = models.DateField()

class Room(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField()
    image = models.ImageField(upload_to='media/images/room/')

    def __str__(self):
        return self.title


class Preview(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='media/images/preview/')

    def __str__(self):
        return f'Preview {self.id}'

class ShopCategory(models.Model):
    title = models.CharField(max_length=100)

class ShopItem(models.Model):
    img = models.ImageField(upload_to='media/images/shop/')
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.IntegerField()
    quantity = models.IntegerField()
    category = models.ForeignKey(ShopCategory, on_delete=models.CASCADE, null=True, related_name='category_shop')

class Basket(models.Model):
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, null=True, related_name='baskets')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, related_name='memberBaskets')
    quantity = models.IntegerField(default=1)
    price = models.IntegerField()


class GetPreviewTags(models.Model):
    description = models.CharField(max_length=40)
    image = models.ImageField(upload_to='media/images/get_preview_tags/')

class Consultation(models.Model):
    numberPhone = models.CharField(max_length=50)

class TimetableCoach(models.Model):
    trainer = models.ForeignKey(Coach,  on_delete=models.CASCADE, null=True, related_name='trainer_timetables')
    member = models.ForeignKey(Member,  on_delete=models.CASCADE, null=True, related_name='member_timetables')
    typeTraining = models.CharField(max_length=50)
    dateTime = models.DateTimeField()
    amount = models.IntegerField( default=0)
    status = models.CharField(max_length=50)

#Платежка
class TimetableCoachPayment(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', _('В ожидании')
        SUCCEEDED = 'succeeded', _('Успешно завершен')
        CANCELED = 'canceled', _('Отменен')
        REFUNDED = 'refunded', _('Возвращен')
        # ... другие статусы по необходимости

    timetableСoach = models.ForeignKey(
        TimetableCoach,
        on_delete=models.CASCADE,
        related_name='timetablecoach_payments',
        verbose_name=_('Расписание тренера')
    )
    paymentId: models.CharField = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name=_('ID платежа в системе шлюза')
    )
    amount: models.IntegerField = models.IntegerField(
        verbose_name=_('Сумма платежа')
    )
    currency: models.CharField = models.CharField(
        max_length=3,
        verbose_name=_('Валюта')
    )
    status: models.CharField = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Статус платежа')
    )
    createdAt: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updatedAt: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        verbose_name = _('Тренер')
        verbose_name_plural = _('Тренера')
        ordering = ('-createdAt',)



class SubscriptionPayment(models.Model):
    class Status(models.TextChoices):
            PENDING = 'pending', _('В ожидании')
            SUCCEEDED = 'succeeded', _('Успешно завершен')
            CANCELED = 'canceled', _('Отменен')
            REFUNDED = 'refunded', _('Возвращен')
            # ... другие статусы по необходимости

    subscription: models.ForeignKey = models.ForeignKey(
            Subscription,
            on_delete=models.CASCADE,
            related_name='payments',
            verbose_name=_('Заказ')
        )
    paymentID: models.CharField = models.CharField(
            max_length=255,
            unique=True,
            db_index=True,
            verbose_name=_('ID платежа в системе шлюза')
        )
    amount: models.DecimalField = models.DecimalField(
            max_digits=10,
            decimal_places=0,
            verbose_name=_('Сумма платежа')
        )
    currency: models.CharField = models.CharField(
            max_length=3,
            verbose_name=_('Валюта')
        )
    status: models.CharField = models.CharField(
            max_length=20,
            choices=Status.choices,
            default=Status.PENDING,
            verbose_name=_('Статус платежа')
        )
    createdAt: models.DateTimeField = models.DateTimeField(
            auto_now_add=True,
            verbose_name=_('Дата создания')
        )
    updatedAat: models.DateTimeField = models.DateTimeField(
            auto_now=True,
            verbose_name=_('Дата обновления')
        ),
    class Meta:
            verbose_name = _('Платеж')
            verbose_name_plural = _('Платежи')
            ordering = ('-createdAt',)

class BuyItem(models.Model):
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, null=True, related_name='buyItems')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, related_name='memberBuyItems')
    date = models.DateTimeField(default=timezone.now)

class ShopPayment(models.Model):
    class Status(models.TextChoices):
            PENDING = 'pending', _('В ожидании')
            SUCCEEDED = 'succeeded', _('Успешно завершен')
            CANCELED = 'canceled', _('Отменен')
            REFUNDED = 'refunded', _('Возвращен')
            # ... другие статусы по необходимости

    item: models.ForeignKey = models.ForeignKey(
            ShopItem,
            on_delete=models.CASCADE,
            related_name='payments',
            verbose_name=_('Заказ')
        )
    paymentID: models.CharField = models.CharField(
            max_length=255,
            unique=True,
            db_index=True,
            verbose_name=_('ID платежа в системе шлюза')
        )
    amount: models.DecimalField = models.IntegerField(

            verbose_name=_('Сумма платежа')
        )
    currency: models.CharField = models.CharField(
            max_length=3,
            verbose_name=_('Валюта')
        )
    quantity: models.IntegerField = models.IntegerField(
        default=1,
        verbose_name=_('Количество')
    )
    status: models.CharField = models.CharField(
            max_length=20,
            choices=Status.choices,
            default=Status.PENDING,
            verbose_name=_('Статус платежа')
        )
    createdAt: models.DateTimeField = models.DateTimeField(
            auto_now_add=True,
            verbose_name=_('Дата создания')
        )
    updatedAat: models.DateTimeField = models.DateTimeField(
            auto_now=True,
            verbose_name=_('Дата обновления')
        ),
    class Meta:
            verbose_name = _('Платеж')
            verbose_name_plural = _('Платежи')
            ordering = ('-createdAt',)

class BuySubscription(models.Model):
    buySubscription = models.ForeignKey(SubscriptionPayment,  on_delete=models.CASCADE, null=True, related_name='purchases')
    startDate = models.DateField(default=timezone.now)
    endDate = models.DateField()
    personalCard = models.ForeignKey(PersonalCard, on_delete=models.CASCADE, null=True, related_name='personal_card_subscriptions')
    isActive = models.BooleanField(default=True)