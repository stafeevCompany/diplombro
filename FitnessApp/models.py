from django.utils import timezone
from django.db import models
from django.utils.translation import gettext_lazy as _

class Role(models.Model):
    name = models.CharField(max_length=50, default="Пользователь", unique=True)

    def __str__(self):
        return self.name


class User(models.Model):
    role = models.ForeignKey(Role,  on_delete=models.CASCADE, null=True, related_name='users')
    phone = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)



class SubscriptionCategory(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    category = models.ForeignKey(SubscriptionCategory,  on_delete=models.CASCADE, null=True, related_name='category_subscriptions')
    title = models.CharField(max_length=50)
    duration_days = models.PositiveIntegerField()
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
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    phone = models.CharField(max_length=50, unique=True)
    passport_data = models.CharField(max_length=11)
    image = models.ImageField(upload_to='media/images/members/')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class PersonalCard(models.Model):
    code = models.CharField(max_length=50, unique=True)
    qr_code = models.ImageField(upload_to='media/images/qr_codes/')
    member = models.ForeignKey(Member,  on_delete=models.CASCADE, null=True, related_name='cards')
    def __str__(self):
        return self.code

class Visit(models.Model):
    member = models.ForeignKey(Member,  on_delete=models.CASCADE, null=True, related_name='visits')
    visitDate = models.DateTimeField(default=timezone.now)

class BuySubscription(models.Model):
    subscription = models.ForeignKey(Subscription,  on_delete=models.CASCADE, null=True, related_name='purchases')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    personal_card = models.ForeignKey(PersonalCard, on_delete=models.CASCADE, null=True, related_name='personal_card_subscriptions')
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return f'{self.subscription} from {self.start_date} to {self.end_date}'


class Notification(models.Model):
    user = models.ForeignKey(User,  on_delete=models.CASCADE, null=True, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    text = models.TextField()
    is_read = models.BooleanField(default=False)

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
    user = models.ForeignKey(User,  on_delete=models.CASCADE, related_name='coach')
    image = models.ImageField(upload_to='media/images/coach/')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50)
    passport_data = models.CharField(max_length=11)
    phone = models.CharField(max_length=50, unique=True)
    experience = models.TextField()
    date_of_birth = models.DateField()
    coach_type = models.ForeignKey(CoachType, on_delete=models.SET_NULL, null=True, related_name='type')
    price = models.IntegerField()

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
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50)
    passport_data = models.CharField(max_length=11)
    phone = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField()

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
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    category = models.ForeignKey(ShopCategory, on_delete=models.CASCADE, null=True, related_name='category_shop')

class Basket(models.Model):
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, null=True, related_name='baskets')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, related_name='memberBaskets')
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)


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
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=50)

#Платежка
class TimetableCoachPayment(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', _('В ожидании')
        SUCCEEDED = 'succeeded', _('Успешно завершен')
        CANCELED = 'canceled', _('Отменен')
        REFUNDED = 'refunded', _('Возвращен')
        # ... другие статусы по необходимости

    timetable_coach = models.ForeignKey(
        TimetableCoach,
        on_delete=models.CASCADE,
        related_name='timetablecoach_payments',
        verbose_name=_('Расписание тренера')
    )
    payment_id: models.CharField = models.CharField(
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
    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        verbose_name = _('Тренер')
        verbose_name_plural = _('Тренера')
        ordering = ('-created_at',)



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
    payment_id: models.CharField = models.CharField(
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
    created_at: models.DateTimeField = models.DateTimeField(
            auto_now_add=True,
            verbose_name=_('Дата создания')
        )
    updated_at: models.DateTimeField = models.DateTimeField(
            auto_now=True,
            verbose_name=_('Дата обновления')
        ),
    class Meta:
            verbose_name = _('Платеж')
            verbose_name_plural = _('Платежи')
            ordering = ('-created_at',)

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
    payment_id: models.CharField = models.CharField(
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
    created_at: models.DateTimeField = models.DateTimeField(
            auto_now_add=True,
            verbose_name=_('Дата создания')
        )
    updated_at: models.DateTimeField = models.DateTimeField(
            auto_now=True,
            verbose_name=_('Дата обновления')
        ),
    class Meta:
            verbose_name = _('Платеж')
            verbose_name_plural = _('Платежи')
            ordering = ('-created_at',)