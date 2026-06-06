from django import forms

from .models import *

class LoginForm(forms.Form):
    phone = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)

class RegistrationForm(forms.Form):
    lastname = forms.CharField(max_length=15)
    firstname = forms.CharField(max_length=15)
    patronymic = forms.CharField(max_length=15)
    phone = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)
    birthday = forms.DateField(widget=forms.DateInput)
    email = forms.EmailField(widget=forms.EmailInput)


class QuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)

class EditProfileForm(forms.Form):
    image = forms.ImageField()
    firstname = forms.CharField(max_length=15)
    lastname = forms.CharField(max_length=15)
    patronymic = forms.CharField(max_length=15)
    phone = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.CharField(max_length=15)

class ConcultationForm(forms.Form):
    phone = forms.CharField(max_length=15)


class RecordTranningForm(forms.Form):
    dateTime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'style': 'width: 300px; border: none; border-bottom: 2px solid black; font-size: 20px'
        }))


class VisitAddForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['member', 'visitDate']
        widgets = {
            'visitDate': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'member': 'Клиент',
            'visitDate': 'Дата посещения',
        }

class TimetableCoachForm(forms.ModelForm):
    class Meta:
        model = TimetableCoach
        fields = ['trainer', 'member','typeTraining', 'dateTime', 'status']
        widgets = {
            'dateTime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'trainer': "Тренер",
            'member': 'Клиент',
            'dateTime': 'Запись',
            'status': "Статус",
            'typeTraining': "Тип тренировки",

        }

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['title', 'description', 'image']
        labels = {
            'title': "Название",
            'description': 'Описание',
            'image': 'Изображение',

        }

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['image', 'title', 'content', 'date']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'title': "Название",
            'content': 'Описание',
            'image': 'Изображение',
            'date': "Дата создания"

        }

class CoachForm(forms.ModelForm):
    class Meta:
        model = Coach
        fields = [
            'user',
            'image',
            'firstName',
            'lastName',
            'patronymic',
            'passportData',
            'phone',
            'experience',
            'dateOfBirth',
            'coachType',
            'price'
        ]
        labels = {
            'user': 'Пользователь',
            'image': 'Фото',
            'firstName': 'Фамилия',
            'lastName': 'Имя',
            'patronymic': 'Отчество',
            'passportData': 'Паспортные данные',
            'phone': 'Телефон',
            'experience': 'Опыт',
            'dateOfBirth': 'Дата рождения',
            'coachType': 'Тип',
            'price': 'Цена'

        }
        widgets = {
            'dateOfBirth': forms.DateInput(attrs={'type': 'date'}),
        }

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['category','title','durationDays','price',]

    labels = {
        'category': "Категория", 'title': "Название", 'durationDays': "Длительность в днях", 'price': "Цена",

    }

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            'user',
            'image',
            'firstName',
            'lastName',
            'patronymic',
            'passportData',
            'phone',
            'dateOfBirth',
        ]
        labels = {
            'user': 'Пользователь',
            'image': 'Фото',
            'firstName': 'Фамилия',
            'lastName': 'Имя',
            'patronymic': 'Отчество',
            'passportData': 'Паспортные данные',
            'phone': 'Телефон',
            'dateOfBirth': 'Дата рождения',
        }
        widgets = {
            'dateOfBirth': forms.DateInput(attrs={'type': 'date'}),
        }


class CoachTypeForm(forms.ModelForm):
    class Meta:
        model = CoachType
        fields = ['name']

    labels = {
        'name': "Название",

    }

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['name', 'trainer']
        labels = {
            'name': "Образование",
            'trainer': 'Тренер',

        }
class DirectionForm(forms.ModelForm):
    class Meta:
        model = Direction
        fields = ['name', 'trainer']
        labels = {
            'name': "Направление",
            'trainer': 'Тренер',
        }

# Форма для SubscriptionCategory
class SubscriptionCategoryForm(forms.ModelForm):
    class Meta:
        model = SubscriptionCategory
        fields = ['name']
        labels = {
            'name': 'Название категории подписки',
        }



# Форма для User
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['role', 'phone', 'password', 'isActive', 'dateJoined']
        widgets = {
            'password': forms.PasswordInput(),
            'dateJoined': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'role': 'Роль пользователя',
            'phone': 'Телефон',
            'password': 'Пароль',
            'isActive': 'Активен',
            'dateJoined': 'Дата регистрации',
        }

# Форма для ShopCategory
class ShopCategoryForm(forms.ModelForm):
    class Meta:
        model = ShopCategory
        fields = ['title']
        labels = {
            'title': 'Название категории магазина',
        }

# Форма для ShopItem
class ShopItemForm(forms.ModelForm):
    class Meta:
        model = ShopItem
        fields = ['img', 'title', 'description', 'price', 'quantity', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'img': 'Изображение',
            'title': 'Название товара',
            'description': 'Описание',
            'price': 'Цена',
            'quantity': 'Количество',
            'category': 'Категория',
        }

# Форма для PersonalCard
class PersonalCardForm(forms.ModelForm):
    class Meta:
        model = PersonalCard
        fields = ['code', 'qrCode', 'member']
        labels = {
            'code': 'Код карты',
            'qrCode': 'QR-код',
            'member': 'Клиент',
        }

class SubscriptionFeatureForm(forms.ModelForm):
    class Meta:
        model = SubscriptionFeature
        fields = ['subscription', 'name']
        labels = {
            'subscription': 'Абонемент',
            'name': 'Возможность',
        }

class ReviewForm(forms.Form):
    review_text = forms.CharField(widget=forms.Textarea)