from enum import member

from dateutil.relativedelta import relativedelta
from django.db.models import Count, Q
from django.shortcuts import *
import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from rest_framework import generics

from django.apps import apps
from .forms import *
import json
from datetime import timedelta, datetime
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDate
from collections import defaultdict
from django.utils import timezone
from .utils import send_email

now = timezone.now()

def create_notification(user, title, text):
    Notification.objects.create(user=user, title=title, text=text)

from django_celery_beat.models import PeriodicTask, IntervalSchedule

def check_and_award_achievement(user, achievement_name):
    # Получаем достижение по имени
    achievement = Achievement.objects.filter(name=achievement_name).first()
    if not achievement:
        return

    # Проверяем, есть ли уже это достижение у пользователя
    already_earned = UserAchievement.objects.filter(user=user, achievement=achievement).exists()
    if not already_earned:
        # Выдаем достижение
        UserAchievement.objects.create(user=user, achievement=achievement)
        # Можно добавить уведомление или лог
        print(f'Пользователь {user} получил достижение: {achievement.name}')


task_name = 'Send training reminders every hour'
# Создаем интервал, если его еще нет
every_hour, created = IntervalSchedule.objects.get_or_create(
    every=1,
    period=IntervalSchedule.HOURS,
)
# Проверяем, есть ли уже задача с таким именем
if not PeriodicTask.objects.filter(name=task_name).exists():
    PeriodicTask.objects.create(
        interval=every_hour,
        name=task_name,
        task='FitnessApp.tasks.send_training_reminders',
    )
else:
    print(f"Задача с названием '{task_name}' уже существует.")

from FitnessApp.tasks import send_training_reminders




#Авторизация
def login(request):
    error = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            login = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(phone=login)
                if user.password == password :
                    user.isActive = True
                    user.save()
                    # Записываем данные пользователя в сессию
                    request.session['user_id'] = user.id
                    request.session['phone'] = user.phone
                    request.session['role'] = user.role.name
                    request.session['active'] = user.isActive
                    user.date_joined = timezone.now()

                    if user.role.name == "Администратор":
                        return redirect('adminMainPage')
                    elif user.role.name == "Тренер":
                        return redirect('mainTrainerPage')
                    elif user.role.name == "Пользователь":
                        member = Member.objects.get(phone=login)
                        request.session['email'] = member.email
                        return redirect('main_page')

                else:
                    error = 'Неверный пароль'
            except User.DoesNotExist:
                error = 'Пользователь не найден'
        else:
            error = 'Некорректные данные формы'
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form, 'error': error})

def registration(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            context = {

                'user': user,

            }
            return render(request, 'user/profile_user.html', context)
    else:
        request.session.clear()
    error = None
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            lastname = form.cleaned_data['lastname']
            firstname = form.cleaned_data['firstname']
            patronymic = form.cleaned_data['patronymic']
            login = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            birthday = form.cleaned_data['birthday']
            email = form.cleaned_data['email']

            new_user =User.objects.create(
                    password=password,
                    phone=login,
                    isActive = False,
                    role_id=1

            )

            Member.objects.get_or_create(
                user=new_user,
                lastName=lastname,
                firstName=firstname,
                patronymic=patronymic,
                dateOfBirth=birthday,
                phone=login,
                email = email,

            )
            PersonalCard.objects.get_or_create(
                 member_id=Member.objects.get(phone=login).id
            )

            return redirect('login')

    else:
        request.session.clear()
        form = RegistrationForm()
    return render(request, 'auth/registration.html', {'form': form, 'error': error})


#Тренер
def mainTrainerPage(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            trainerData = Coach.objects.get(user_id=user.id)
            today = timezone.now().date()
            nearest_training = TimetableCoach.objects.filter(
                trainer=trainerData,
                dateTime__gte=timezone.now()
            ).order_by('dateTime').first()
            start_date = now - timedelta(days=6)

            dates = [start_date + timedelta(days=i) for i in range(7)]
            visits_per_day = []

            for date in dates:
                count = TimetableCoach.objects.filter(
                    trainer=trainerData,
                    dateTime__date=date.date()
                ).count()
                # преобразуем date в строку в формате ISO
                date_str = date.date().isoformat()
                visits_per_day.append({'date': date_str, 'count': count})
            # Передача данных в шаблон как JSON
            visits_json = json.dumps(visits_per_day)


            # Первый день месяца
            first_day_of_month = today.replace(day=1)

            # Последний день следующего месяца (или можно использовать следующий месяц)
            # Для этого используем следующую логику:
            if today.month == 12:
                next_month = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_month = today.replace(month=today.month + 1, day=1)

            # Фильтрация оплат за текущий месяц
            monthly_payments = TimetableCoachPayment.objects.filter(
                created_at__gte=first_day_of_month,
                created_at__lte=next_month,
                timetable_coach__trainer=trainerData
            )

            # Суммирование суммы
            total_earnings = float(monthly_payments.aggregate(total=Sum('amount'))['total'] or 0) * 0.6

            trainings_this_month = TimetableCoach.objects.filter(
                trainer=trainerData,
                dateTime__gte=first_day_of_month,
                dateTime__lt=next_month
            ).count()

            visitsTopMembers = TimetableCoach.objects.all().order_by('dateTime').distinct().first()
            # Получить участников, у которых есть тренировки с данным тренером, и отсортировать по количеству
            visits_often_members = Member.objects.annotate(
                training_count=Count('member_timetables', filter=Q(member_timetables__trainer=trainerData))
            ).filter(
                training_count__gt=0
            ).order_by('-training_count')

            end_month = datetime.now().replace(day=1)
            start_month = end_month - relativedelta(months=6)

            # Получение платежей по тренировкам за последние 6 месяцев
            training_payments = (
                TimetableCoachPayment.objects
                .filter(
                    timetable_coach__trainer=trainerData,

                )
                .annotate(month=TruncMonth('createdAt'))
                .values('month')
                .annotate(total=Sum('amount')*0.6)
                .order_by('month')
            )
            # Создаем словарь по месяцам
            all_months = []
            current_month = start_month
            while current_month <= end_month:
                all_months.append(current_month)
                current_month += relativedelta(months=1)

            monthly_totals = {}
            for month in all_months:
                monthly_totals[month.strftime('%Y-%m')] = {'training': 0}

            # Заполняем суммами из базы
            for entry in training_payments:
                month_str = entry['month'].strftime('%Y-%m')
                if month_str in monthly_totals:
                    monthly_totals[month_str]['training'] = entry['total']

            # Формируем данные для графика
            dps3 = []
            for month in all_months:
                label = month.strftime('%B %Y')
                month_str = month.strftime('%Y-%m')
                total = monthly_totals[month_str]['training']
                dps3.append({'label': label, 'y': total})


            context = {
                'data_points3': json.dumps(dps3),
                "visits_json": visits_json,
                "nearest_training": nearest_training,
                "visitsTopMembers":visitsTopMembers,
                "visits_often_members": visits_often_members,

                "trainings_this_month":trainings_this_month,
                "trainer": trainerData,
                'user': user,
                "total_training_payment": total_earnings

            }
            return render(request, 'trainer/mainTrainerPage.html', context)
    else:
        request.session.clear()
        return render(request, 'auth/login.html')



def get_schedule_for_day(target_date, trainerData):
    start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return TimetableCoach.objects.filter(dateTime__gte=start, dateTime__lt=end, trainer=trainerData).order_by('dateTime')

def get_today_schedule(trainerData):
    now = timezone.now()
    return get_schedule_for_day(now, trainerData)

def get_tomorrow_schedule(trainerData):
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    return get_schedule_for_day(tomorrow, trainerData)

def get_week_schedule(coach):

    now = timezone.now()
    start_of_week = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=7)
    return TimetableCoach.objects.filter(dateTime__gte=start_of_week, dateTime__lt=end_of_week,trainer=coach).order_by('dateTime')

def group_schedule_by_date(schedule_queryset):
    grouped = defaultdict(list)
    for item in schedule_queryset:
        date_str = item.dateTime.strftime('%d.%m.%Y')
        grouped[date_str].append(item)
    return dict(grouped)

def recordTrainerTimeTable(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            trainerData = Coach.objects.get(user_id=user.id)

            today = get_today_schedule(trainerData)
            tomorrow = get_tomorrow_schedule(trainerData)
            week = get_week_schedule(trainerData)

            context = {
                'today_schedule': group_schedule_by_date(today),
                'tomorrow_schedule': group_schedule_by_date(tomorrow),
                'week_schedule': group_schedule_by_date(week),

                "trainer": trainerData,
                'user': user,

            }
            return render(request, 'trainer/recordsTrainerTimeTable.html', context)
    else:
        request.session.clear()
        return render(request, 'auth/login.html')







#Админка
def adminMainPage(request):
    # Получение дат
    today = timezone.now().date()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]  # последние 7 дней
    user_id = request.session.get('user_id')


    if user_id:
        user = User.objects.get(id=user_id)
        countTrainers = Coach.objects.all().count()
        member = Member.objects.all().count()
        visitsTopMembers = Visit.objects.all().order_by('visitDate').distinct().first()
        visits_often_members = Member.objects.annotate(
            visits_count=Count('visits')
        ).order_by('-visits_count')

        # Определяем диапазон месяцев
        end_month = datetime.now().replace(day=1)
        start_month = end_month - relativedelta(months=6)

        all_months = []
        current_month = start_month
        while current_month <= end_month:
            all_months.append(current_month)
            current_month += relativedelta(months=1)
        if user:

            # Платежи по тренировкам
            training_payments = (
                TimetableCoachPayment.objects
                .annotate(month=TruncMonth('createdAt'))
                .values('month')
                .annotate(total=Sum('amount'))
                .order_by('month')
            )

            # Платежи по подпискам
            subscription_payments = (
                SubscriptionPayment.objects
                .annotate(month=TruncMonth('createdAt'))
                .values('month')
                .annotate(total=Sum('amount'))
                .order_by('month')
            )
            shop_payments = (
                ShopPayment.objects
                .annotate(month=TruncMonth('createdAt'))
                .values('month')
                .annotate(total=Sum('amount'))
                .order_by('month')
            )

            monthly_totals = {}
            for month in all_months:
                # Используем форматирование, чтобы сравнивать одинаково
                monthly_totals[month.strftime('%Y-%m')] = {'training': 0, 'subscription': 0, 'shop': 0}

            # Обновляем с платежами по тренировкам
            for entry in training_payments:
                month_str = entry['month'].strftime('%Y-%m')
                if month_str in monthly_totals:
                    monthly_totals[month_str]['training'] = float(entry['total'])

            # Обновляем с платежами по подпискам
            for entry in subscription_payments:
                month_str = entry['month'].strftime('%Y-%m')
                if month_str in monthly_totals:
                    monthly_totals[month_str]['subscription'] = float(entry['total'])

             # Обновляем с платежами по подпискам
            for entry in shop_payments:
                month_str = entry['month'].strftime('%Y-%m')
                if month_str in monthly_totals:
                    monthly_totals[month_str]['shop'] = float(entry['total'])

            # Формируем данные для графика
            dps1 = []
            for month in all_months:
                label = month.strftime('%B %Y')
                month_str = month.strftime('%Y-%m')
                total = (monthly_totals[month_str]['training'] +
                         monthly_totals[month_str]['subscription']
                         + monthly_totals[month_str]['shop'])
                dps1.append({'label': label, 'y': total})

            adminData = Administrator.objects.get(user_id=user.id)
            subscription_payments = SubscriptionPayment.objects.all().filter(createdAt__gte=start_month)
            training_payments = TimetableCoachPayment.objects.all().filter(createdAt__gte=start_month)
            shop_payments = ShopPayment.objects.all().filter(createdAt__gte=start_month)

            total_subscription_payment = sum(sp.amount for sp in subscription_payments)
            total_training_payment = sum(tp.amount for tp in training_payments)
            total_shop_payment = sum(tp.amount for tp in shop_payments)
            money = total_subscription_payment + total_training_payment+total_shop_payment

            subscription_payments_today = SubscriptionPayment.objects.all().filter(createdAt__gte=now.date())
            training_payments_today = TimetableCoachPayment.objects.all().filter(createdAt__gte=now.date())
            shop_payments_today = ShopPayment.objects.all().filter(createdAt__gte=now.date())

            total_subscription_payment_today = sum(sp.amount for sp in subscription_payments_today)
            total_training_payment_today = sum(tp.amount for tp in training_payments_today)
            total_shop_payment_today = sum(tp.amount for tp in shop_payments_today)
            money_today = total_subscription_payment_today + total_training_payment_today+total_shop_payment_today

            data_points = []
            labels = []
            for date in dates:
                count = Visit.objects.filter(visitDate__date=date).count()
                labels.append(date.strftime('%Y-%m-%d'))  # или '%Y-%m-%d'
                data_points.append({'label': date.strftime('%Y-%m-%d'), 'y': count})

            context = {
                'data_points_total': json.dumps(dps1),
                'labels': json.dumps(labels),
                'data_points': json.dumps(data_points),
                "admin": adminData,
                'user': user,
                'countTrainers': countTrainers,
                "countMembers": member,
                "money_today": money_today,
                "money": money,
                "visitsOftenMember": visits_often_members,
                "topVisitsOftenMember":visitsTopMembers
            }
            return render(request, 'admin/mainAdmin.html', context)
    else:
        request.session.clear()
        return render(request, 'auth/login.html')

def workSite(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            adminData = Administrator.objects.get(user_id=user.id)
            preview = Preview.objects.all()
            rooms = Room.objects.all()
            getPreviewTags = GetPreviewTags.objects.all()
            cosl = Consultation.objects.all()
            context = {
                'conl': cosl,
                "admin": adminData,
                'user': user,
                "preview": preview,
                "rooms": rooms,
                'getPreviewTags': getPreviewTags
            }
            return render(request, 'admin/page/WorkSite.html', context)
    else:
        request.session.clear()
        return render(request, 'auth/login.html')

def WorkTable(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')
    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    members = Member.objects.all()
    trainers = Coach.objects.all()
    news = News.objects.all()
    subscriptions = Subscription.objects.all()

    users = User.objects.all()
    educationTrainers = Education.objects.all()
    directionTrainers = Direction.objects.all()
    shopItems = ShopItem.objects.all()
    shopCategoryItems = ShopCategory.objects.all()
    featers = SubscriptionFeature.objects.all()
    persCard = PersonalCard.objects.all()
    # Собираем все особенности подписок
    subscriptions_features = {}
    for subscription in subscriptions:
        features = subscription.features.all()
        subscriptions_features[subscription.id] = features

    members_data = []

    for member in members:
        personal_cards = PersonalCard.objects.filter(member=member)
        personal_card = personal_cards.first() if personal_cards.exists() else None

        trainers_data = []

        for trainer in trainers:
            directions = trainer.directions.all()
            educations = trainer.educations.all()
            trainers_data.append({
                'trainer': trainer,
                'directions': directions,
                'educations': educations,
            })

        members_data.append({
            'member': member,
            'personal_card': personal_card,
            'trainers': trainers_data
        })

    context = {
        'persCard':persCard,
        "featers": featers,
        'users': users,
        'educationTrainers': educationTrainers,
        'directionTrainers': directionTrainers,
        'shopItems': shopItems,
        'shopCategoryItems': shopCategoryItems,

        "admin": adminData,
        'user': user,
        'members': members_data,
        'news': news,
        'subscriptions': subscriptions,
        'subscriptions_features': subscriptions_features,
    }

    return render(request, 'admin/page/AdminTables.html', context)

def paymentsTable(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        trainingPayments = TimetableCoachPayment.objects.all()
        subscriptionPayments = BuySubscription.objects.all()
        shopItemsPayments = ShopPayment.objects.all()
        if user:
            adminData = Administrator.objects.get(user_id=user.id)
            context = {
                "admin": adminData,
                'user': user,
                'shopItemsPayments': shopItemsPayments,
                "trainingPayments": trainingPayments,
                "subscriptionPayments": subscriptionPayments
            }

            return render(request, 'admin/page/PaymentsTable.html', context)
    else:
        request.session.clear()
        return render(request, 'auth/login.html')

def visitsTable(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        visits = Visit.objects.all()

        if user:
            adminData = Administrator.objects.get(user_id=user.id)
            context = {
                "admin": adminData,
                'user': user,
                "visits": visits,
            }
            return render(request, 'admin/page/VisitsTable.html', context)
    else:
        request.session.clear()
        return render(request, 'auth/login.html')

def get_schedule_for_dayAdmin(target_date):
    start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return TimetableCoach.objects.filter(dateTime__gte=start, dateTime__lt=end).order_by('dateTime')

def get_today_scheduleAdmin(target_date):
    now = timezone.now()
    return get_schedule_for_dayAdmin(now)

def get_tomorrow_scheduleAdmin():
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    return get_schedule_for_dayAdmin(tomorrow)

def get_week_scheduleAdmin():
    now = timezone.now()
    start_of_week = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=7)
    return TimetableCoach.objects.filter(dateTime__gte=start_of_week, dateTime__lt=end_of_week).order_by('dateTime')

def group_schedule_by_dateAdmin(schedule_queryset):
    grouped = defaultdict(list)
    for item in schedule_queryset:
        date_str = item.dateTime.strftime('%d.%m.%Y')
        grouped[date_str].append(item)
    return dict(grouped)

def timeTable(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            adminData = Administrator.objects.get(user_id=user.id)
            today = get_today_scheduleAdmin(target_date=timezone.now())
            tomorrow = get_tomorrow_scheduleAdmin()
            week = get_week_scheduleAdmin()

            context = {
                'today_schedule': group_schedule_by_date(today),
                'tomorrow_schedule': group_schedule_by_date(tomorrow),
                'week_schedule': group_schedule_by_date(week),

                "admin": adminData,
                'user': user,
            }
            return render(request, 'admin/recordsTrainerTimeTable.html', context)
    else:
        request.session.clear()
        return render(request, 'auth/login.html')

#Для пользователя
def main_page(request):
    user_id = request.session.get('user_id')
    rooms = Room.objects.all()
    news = News.objects.order_by('date').all()
    trainers = Coach.objects.all()
    preview = Preview.objects.all()
    getYouTags = GetPreviewTags.objects.all()
    subscriptions = Subscription.objects.all()

    if request.method == 'POST':
        form = ConcultationForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone']
            Consultation.objects.create(
                numberPhone=phone_number,
            )
            # Обработка номера телефона (сохранение, отправка и т.п.)
            return redirect('main_page')  # или другая страница

    if user_id:

        user = User.objects.get(id=user_id)

        if user:
            if request.session.get('role') == 'Пользователь':
                memberData = Member.objects.get(user_id=user.id)
                context = {
                    "news": news,
                    "rooms": rooms,
                    "preview": preview,
                    'user': user,
                    "trainers": trainers,
                    "getYouTags": getYouTags,
                    'subscriptions': subscriptions,
                    'member': memberData,


                }
                return render(request, 'mainPage/index.html', context)
    else:
        request.session.clear()
        context = {
            "news": news,
            "rooms": rooms,
            "preview": preview,
            "trainers": trainers,
            'subscriptions': subscriptions,
            "getYouTags": getYouTags,

        }
        return render(request, 'mainPage/index.html', context)

def achivmentsUser(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            member = Member.objects.get(user_id=user.id)
            achivments = Achievement.objects.all()

            context = {
                'member': member,
                'user': user,
                'achivments': achivments,

            }
            return render(request, './user/achivmentsUser.html', context)

def achivmentsPage(request, id):
    user_id = request.session.get('user_id')
    achivment = get_object_or_404(Achievement, id=id)

    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            member = Member.objects.get(user_id=user.id)
            context = {
                'member': member,
                'user': user,
                'achivment': achivment,

            }
            return render(request, './page/achivmentsPage.html', context)
def shop(request):
    user_id = request.session.get('user_id')
    item = ShopItem.objects.all()
    category = ShopCategory.objects.filter(category_shop__in=item).distinct()
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            member = Member.objects.get(user_id=user.id)

            context = {
                'member': member,
                'user': user,
                'categoryItem': category,
                'items': item,

            }
            return render(request, './catallogs/shop.html', context)
    else:
        request.session.clear()
        context = {
            "items": item,
            "category": category
        }
        return render(request, './catallogs/shop.html', context)

def pageItem(request, id):
    user_id = request.session.get('user_id')
    item = get_object_or_404(ShopItem, id=id)

    if not user_id:
        return redirect('login')

    user = User.objects.get(id=user_id)
    memberData = Member.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = QuantityForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            action = request.POST.get('action')

            if action == 'add_to_cart':
                # Проверяем, есть ли уже такой товар в корзине у этого пользователя
                basket_item, created = Basket.objects.get_or_create(
                    item=item,
                    member=memberData,
                    defaults={'quantity': quantity, 'price': quantity * item.price}
                )
                if not created:
                    # Если товар уже есть, обновляем количество
                    basket_item.quantity += quantity
                    basket_item.price = basket_item.quantity * item.price
                    basket_item.save()
                # Можно добавить сообщение о успешном добавлении
                return redirect('shop')  # или другая страница

            elif action == 'buy_now':
                # Создаем корзину или заказ и перенаправляем на оформление
                product = Basket.objects.create(
                    item=item,
                    quantity=quantity,
                    member=memberData,
                    price=quantity * item.price,
                )
                return redirect('buyItem', id=product.id)

        else:
            # Обработка ошибок формы
            context = {
                'user': user,
                'member': memberData,
                'item': item,
                'form': form,
            }
            return render(request, './page/pageItem.html', context)
    else:
        form = QuantityForm()
        context = {
            'user': user,
            'member': memberData,
            'item': item,
            'form': form,
        }
        return render(request, './page/pageItem.html', context)

def buyItem(request, id):
    user_id = request.session.get('user_id')
    try:
        item = Basket.objects.get(id=id)
    except Basket.DoesNotExist:
        return redirect('shop')
    if not user_id:
        return redirect('login')

    user = User.objects.filter(id=user_id).first()
    memberData = Member.objects.get(user_id=user.id)

    context = {
        'user': user,
        'member': memberData,
        'item': item,
        'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'user/function/buyItem.html', context)

def deleteItem(request, id):
    item = Basket.objects.get(id=id)
    item.delete()
    return redirect('basket')

def notification(request):
    send_training_reminders()
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            notifications = Notification.objects.filter(user_id=user.id).order_by("-createdAt")
            if user.role.name == "Администратор":
                admin = Administrator.objects.get(user_id=user.id)
                context = {
                    "notifications": notifications,

                    'admin': admin,

                    'user': user,
                }
                return render(request, 'notification.html', context)
            if user.role.name == "Тренер":
                trainer = Coach.objects.get(user_id=user.id)
                context = {
                    "notifications": notifications,
                    'trainer': trainer,
                    'user': user,
                }
                return render(request, 'notification.html', context)
            if user.role.name == "Пользователь":
                member = Member.objects.get(user_id=user.id)
                context = {
                    "notifications": notifications,
                    'member': member,
                    'user': user,
                }




                return render(request, 'notification.html', context)
    else:
        request.session.clear()
        return render(request, 'auth/login.html')

def subscriptions(request):
    user_id = request.session.get('user_id')
    subscriptions = Subscription.objects.all().prefetch_related('features')
    category =SubscriptionCategory.objects.filter(category_subscriptions__in=subscriptions).distinct()

    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            if request.session.get('role') == 'Пользователь':
                memberData = Member.objects.get(user_id=user.id)
                context = {
                    "subscriptions": subscriptions,
                    'user': user,
                    'member': memberData,
                    "category":category
                }
                return render(request, 'catallogs/subscriptions.html', context)
    else:
        request.session.clear()
        context = {
                "subscriptions": subscriptions,
                "category": category
            }
        return render(request, 'catallogs/subscriptions.html',context)

def page_trainer(request,id):
    user_id = request.session.get('user_id')
    trainer = get_object_or_404(Coach, id=id)
    education = Education.objects.filter(trainer_id=trainer.id)
    direction = Direction.objects.filter(trainer_id=trainer.id)
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            member = Member.objects.get(user_id=user.id)
            review = Review.objects.filter(trainer=trainer).select_related('user')
            if request.method == 'POST':
                form = RecordTranningForm(request.POST)
                if form.is_valid():
                    datetime = form.cleaned_data['dateTime']
                    TimetableCoach.objects.create(
                        trainer=trainer,
                        member=Member.objects.get(user_id=user.id),
                        dateTime=datetime,
                        typeTraining = trainer.coachType,
                        amount=trainer.price,
                        status="Оплачено"

                    )
                    new_record = TimetableCoach.objects.latest('id')
                    return redirect('buyRecord', id=new_record.id)

                form2 = ReviewForm(request.POST)
                if form2.is_valid():
                    review_text = form2.cleaned_data['review_text']
                    Review.objects.create(trainer=trainer, user=member, text=review_text)
                    return redirect(request.path_info)

                else:
                    # Можно показать сообщение или редирект
                    return redirect('login')



            memberData = Member.objects.get(user_id=user.id)
            context = {
                "review": review,
                "direction": direction,
                "trainerPage": trainer,
                "education": education,
                'user': user,
                'member': memberData

            }
            return render(request, 'trainer/../page/pageTrainer.html', context)
    else:
        request.session.clear()
        context = {
            "direction": direction,
            "trainerPage": trainer,
            "education": education,

        }
        return render(request, 'trainer/../page/pageTrainer.html', context)

def page_new(request,id):
    user_id = request.session.get('user_id')
    new = get_object_or_404(News, id=id)
    if user_id:
        user = User.objects.get(id=user_id)
        memberData = Member.objects.get(user_id=user.id)
        if user:
            context = {
                "new": new,
                'user': user,
                'member': memberData,
            }
            return render(request, 'trainer/../page/pageNews.html', context)
    else:
        request.session.clear()
        context = {
            "new": new,
        }
        return render(request, 'trainer/../page/pageNews.html', context)




def news(request):
    user_id = request.session.get('user_id')
    news = News.objects.all()
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            if request.session.get('role') == 'Пользователь':
                memberData = Member.objects.get(user_id=user.id)
                context = {
                    "news": news,
                    'user': user,
                    'member': memberData,
                }
                return render(request, 'catallogs/news.html', context)
    else:
        request.session.clear()
        context = {
            "news": news,
        }
        return render(request, 'user/../catallogs/news.html', context)



def trainers(request):
    user_id = request.session.get('user_id')
    trainers = Coach.objects.all()
    category = CoachType.objects.filter(type__in=trainers).distinct()
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            if request.session.get('role') == 'Пользователь':
                    memberData = Member.objects.get(user_id=user.id)
                    context = {
                        "trainers": trainers,
                        'user': user,
                        'member': memberData,
                        "categoryTrainer":category
                    }
                    return render(request, 'catallogs/trainers.html', context)
    else:
        request.session.clear()
        context = {
            "trainers": trainers,
            "categoryTrainer": category
        }
        return render(request, 'page/../catallogs/trainers.html', context)

def buyTrainers(request,id):
    user_id = request.session.get('user_id')
    trainer = get_object_or_404(Coach, id=id)
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            memberData = Member.objects.get(user_id=user.id)
            context = {
                'user': user,
                'member': memberData,
                "trainer":trainer
            }
            return render(request, 'user/function/buySubscription.html', context)

def profile_user(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        member = Member.objects.get(user_id=user.id)
        card = PersonalCard.objects.get(member_id=member.id)
        buyItemShop = BuyItem.objects.all().filter(member=member)

        if user:
            try:
                activeSubscription = BuySubscription.objects.get(personalCard_id=card.id)
                maxVisits = (activeSubscription.endDate - activeSubscription.startDate).days
                visits = Visit.objects.all().filter(
                    member__cards=card,
                    visitDate__gte=activeSubscription.startDate,
                    visitDate__lte=activeSubscription.endDate
                ).annotate(
                    visit_day=TruncDate('visitDate')
                ).values(
                    'visit_day'
                ).distinct().count()
                remainingVisits = visits
            except BuySubscription.DoesNotExist:
                activeSubscription = None
                maxVisits = None
                remainingVisits = None
            visit = Visit.objects.all().filter(member=member).count()

            buySubscriptions = BuySubscription.objects.all().filter(personalCard_id=card.id)

            achievementUser = UserAchievement.objects.all().filter(user_id=user.id)
            context = {
                "achievementUser":achievementUser,
                "buyItemShop":buyItemShop,
                "card": card,
                "member": member,
                'user': user,
                "activeSubscription": activeSubscription,
                "buySubscriptions": buySubscriptions,
                "maxVisits": maxVisits,
                "remainingVisits": remainingVisits

            }
            return render(request, 'user/profile_user.html', context)
    else:
        request.session.clear()
        return redirect(login)

def editProfile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return redirect('login')

    user = get_object_or_404(User, id=user_id)
    member = get_object_or_404(Member, user_id=user.id)

    if request.method == 'POST':
        email = request.POST.get('email')
        lastname = request.POST.get('lastname')
        firstname = request.POST.get('firstname')
        patronymic = request.POST.get('patronymic')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        image = request.FILES.get('image')

        # Проверка уникальности номера телефона
        if user.phone != phone:
            if User.objects.filter(phone=phone).exclude(id=user.id).exists():
                context = {'member': member, 'user': user, 'error': 'Телефон уже используется'}
                return render(request, 'user/function/editProfile.html', context)
            user.phone = phone

        # Обновление пароля, если он был введен

        user.phone = phone
        user.password = password
        user.save()

        # Обновление Member
        member.lastName = lastname
        member.firstName = firstname
        member.patronymic = patronymic
        member.phone = phone
        member.email = email

        if image:
            member.image = image
        member.save()

        return redirect('profile_user')

    context = {
        'member': member,
        'user': user,
    }

    return render(request, 'user/function/editProfile.html', context)

def get_schedule_for_dayUser(target_date, member):
    start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return TimetableCoach.objects.filter(dateTime__gte=start, dateTime__lt=end, member=member).order_by('dateTime')

def get_today_scheduleUser(target_date):
    now = timezone.now()
    return get_schedule_for_dayAdmin(now)

def get_tomorrow_scheduleUser():
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    return get_schedule_for_dayAdmin(tomorrow)

def get_week_scheduleUser(member):
    now = timezone.now()
    start_of_week = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=7)
    return TimetableCoach.objects.filter(dateTime__gte=start_of_week, dateTime__lt=end_of_week, member=member).order_by('dateTime')

def group_schedule_by_dateUser(schedule_queryset):
    grouped = defaultdict(list)
    for item in schedule_queryset:
        date_str = item.dateTime.strftime('%d.%m.%Y')
        grouped[date_str].append(item)
    return dict(grouped)

def records(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        member = Member.objects.get(user_id=user.id)


        today = get_today_scheduleAdmin(target_date=timezone.now())
        tomorrow = get_tomorrow_scheduleAdmin()
        week = get_week_scheduleAdmin()

        context = {
                'today_schedule': group_schedule_by_date(today),
                'tomorrow_schedule': group_schedule_by_date(tomorrow),
                'week_schedule': group_schedule_by_date(week),
                "member": member,
                'user': user,

        }
        return render(request, 'user/recordsUserTimeTable.html', context)
    else:
        request.session.clear()
        return render(request, 'auth/login.html')

#Выход из сессии
def logout(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            user.isActive = False
            request.session.clear()
            user.save()

            return redirect('main_page')



def buySubscriptions(request,id):
    user_id = request.session.get('user_id')
    subscription = get_object_or_404(Subscription, id=id)
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            memberData = Member.objects.get(user_id=user.id)
            context = {
                'user': user,
                'member': memberData,
                "subscription":subscription,
                'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY,

            }
            return render(request, 'user/function/buySubscription.html', context)


# Настройка ключа Stripe (можно также передавать в вызовах API)
stripe.api_key = settings.STRIPE_SECRET_KEY
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
@require_POST
def create_payment_subscription(request, id: int) -> JsonResponse:
    """
    Создает Stripe PaymentIntent для данного заказа.
    Возвращает Client Secret для использования на фронтенде.
    """
    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id)
    try:
        order = get_object_or_404(Subscription, id=id)

        # Сумма в минимальных единицах валюты (например, центы для USD)
        # Убедитесь, что Decimal конвертируется правильно (умножаем на 100 для центов)
        # Создаем PaymentIntent в Stripe
        intent = stripe.PaymentIntent.create(
            amount=order.price*100,
            currency='rub', # Указывайте валюту заказа
            metadata={'order_id': order.id}, # Полезные метаданные
            # automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'}, # Опционально
        )

        # Создаем запись о платеже в нашей БД со статусом pending
        # Используем ID Intent'а как payment_id
        payment = SubscriptionPayment.objects.create(
            subscription=order,
            paymentID=intent.id,
            amount=order.price,
            currency='RUB', # Указывайте валюту заказа
            status=SubscriptionPayment.Status.PENDING
        )
        subscription = Subscription.objects.get(id=payment.subscription.id)
        end_date = timezone.now() + timedelta(days=subscription.durationDays)

        BuySubscription.objects.create(
            buySubscription  = payment,
            endDate = end_date,
            personalCard = PersonalCard.objects.get(member__user=user),
            startDate=timezone.now().date(),
            isActive = True
        )

        title = "С успешным приобретением абонемента"
        text = f'Вы приобрели абонемент "{order.title}" на {order.durationDays} дней по цене {order.price}₽'
        member = Member.objects.get(id=user_id)
        send_email(
            title,
            member.email,
            text,
        )

        create_notification(user, "С успешным приобретением абонемента", f"{order.title} на {order.durationDays} дней по цене {order.price}₽"   )
        return JsonResponse({
            'clientSecret': intent.client_secret,
            'paymentId': payment.paymentID,
            'status': payment.status
        })

    except Subscription.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        # Логирование ошибки необходимо!
        print(f"Ошибка при создании PaymentIntent: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def buyRecord(request,id):
    user_id = request.session.get('user_id')
    record = get_object_or_404(TimetableCoach, id=id)
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            memberData = Member.objects.get(user_id=user.id)
            context = {
                'user': user,
                'member': memberData,
                "record":record,
                'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY,

            }
            return render(request, 'user/function/buyRecodrTrainer.html', context)

@csrf_exempt
@require_POST
def create_payment_recordTrainer(request, id: int) -> JsonResponse:
    """
    Создает Stripe PaymentIntent для данного заказа.
    Возвращает Client Secret для использования на фронтенде.
    """
    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id)
    try:
        order = get_object_or_404(TimetableCoach, id=id)

        # Сумма в минимальных единицах валюты (например, центы для USD)
        # Убедитесь, что Decimal конвертируется правильно (умножаем на 100 для центов)
        # Создаем PaymentIntent в Stripe
        intent = stripe.PaymentIntent.create(

            amount=order.trainer.price*100,
            currency='rub', # Указывайте валюту заказа
            metadata={'order_id': order.id}, # Полезные метаданные
            # automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'}, # Опционально
        )

        # Создаем запись о платеже в нашей БД со статусом pending
        # Используем ID Intent'а как payment_id
        paymentRecord = TimetableCoachPayment.objects.create(
            timetableСoach = order,
            paymentId=intent.id,
            amount = order.trainer.price,
            currency='RUB', # Указывайте валюту заказа
            status=TimetableCoachPayment.Status.PENDING,
        )
        text = f"Тренер {order.trainer.lastName} {order.trainer.firstName} {order.trainer.patronymic} будет ждать вас {order.dateTime} на {order.typeTraining}"
        title = "Вы записались на занятие с тренером"
        create_notification(user, title,
                            text  )

        member = Member.objects.get(id=user_id)
        send_email(
            title,
            member.email,
            text,
        )

        return JsonResponse({
            'clientSecret': intent.client_secret,
            'paymentId': paymentRecord.paymentId,
            'status': paymentRecord.status
        })

    except Subscription.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        # Логирование ошибки необходимо!
        print(f"Ошибка при создании PaymentIntent: {e}")
        return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt
@require_POST
def create_payment_item(request, id: int) -> JsonResponse:
    """
    Создает Stripe PaymentIntent для данного заказа.
    Возвращает Client Secret для использования на фронтенде.
    """
    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id)
    try:
        item = get_object_or_404(Basket, id=id)

        # Сумма в минимальных единицах валюты (например, центы для USD)
        # Убедитесь, что Decimal конвертируется правильно (умножаем на 100 для центов)
        # Создаем PaymentIntent в Stripe
        intent = stripe.PaymentIntent.create(
            amount=item.price*100,
            currency='rub', # Указывайте валюту заказа
            metadata={'order_id': item.id}, # Полезные метаданные
            # automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'}, # Опционально
        )

        # Создаем запись о платеже в нашей БД со статусом pending
        # Используем ID Intent'а как payment_id
        payment = ShopPayment.objects.create(
            item=item.item,
            paymentID=intent.id,
            quantity=item.quantity,
            amount=item.price,
            currency='RUB', # Указывайте валюту заказа
            status=SubscriptionPayment.Status.PENDING
        )
        member = Member.objects.get(user_id=user.id)

        BuyItem.objects.create(
            item = item.item,
            member = member,
        )

        item.delete()


        member.balance = item.price / 100
        member.save()
        title = "Вы купили товар"
        text = f"Вы приобрели товар {item.item.title} в количестве {item.quantity} шт. Вы сможете забрать его у администратора"
        create_notification(user, title,text)
        member = Member.objects.get(id=user_id)

        send_email(
            title,
            member.email,
            text,
        )
        return JsonResponse({
            'clientSecret': intent.client_secret,
            'paymentId': payment.paymentID,
            'status': payment.status
        })

    except Basket.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        # Логирование ошибки необходимо!
        print(f"Ошибка при создании PaymentIntent: {e}")
        return JsonResponse({'error': str(e)}, status=500)



def basket(request):
    user_id = request.session.get('user_id')
    items = Basket.objects.all()
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            memberData = Member.objects.get(user_id=user.id)
            context = {
                'user': user,
                'member': memberData,
                "basketItems": items,
            }
            return render(request, 'user/Basket.html', context)

def add_visit(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)
    if request.method == 'POST':
        form = VisitAddForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('visitsTable')  # замените на нужный вам URL
    else:
        form = VisitAddForm()
    return render(request, 'admin/function/Add/addVisit.html', {'form': form, 'admin': adminData})

def edit_visit(request, id):
    visit = get_object_or_404(Visit, id=id)
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)
    if request.method == 'POST':
        form = VisitAddForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            return redirect('visitsTable')  # замените на нужное имя URL
    else:
        form = VisitAddForm(instance=visit)
    return render(request, 'admin/function/Add/addVisit.html', {'form': form,'admin': adminData})

def delete_visit(request, id):
    visit = get_object_or_404(Visit, id=id)
    visit.delete()
    return redirect('visitsTable')



def add_record(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)

    adminData = Administrator.objects.get(user_id=user.id)
    if request.method == 'POST':
        form = TimetableCoachForm(request.POST)
        if form.is_valid():
            form.save()
            title = "Вы записаны к тренеру"
            text = f"Ваш тренер {form.trainer.lastName} {form.trainer.firstName} {form.trainer.patronymic} будет ждать вас {form.dateTime} на {form.typeTraining}"
            send_email(
                title,
                form.member.email,
                text
            )
            create_notification(form.member.user, title, text)
            return redirect('timeTable')  # замените на нужный вам URL
    else:
        form = TimetableCoachForm()
    return render(request, 'admin/function/Add/addTimeRecord.html', {'form': form, 'admin': adminData})


def edit_timetable_coach(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    timetable = get_object_or_404(TimetableCoach, id=id)
    if request.method == 'POST':
        form = TimetableCoachForm(request.POST, instance=timetable)
        if form.is_valid():
            form.save()
            title = "Ваша запись к тренеру изменена"
            text = f"Ваш тренер {form.trainer.lastName} {form.trainer.firstName} {form.trainer.patronymic} будет ждать вас {form.dateTime} на {form.typeTraining}"
            send_email(
                title,
                form.member.email,
                text
            )
            create_notification(form.member.user,title, text)
            return redirect('timeTable')  # замените на нужное URL
    else:
        form = TimetableCoachForm(instance=timetable)
    return render(request, 'admin/function/Add/addTimeRecord.html', {'form': form, 'admin': adminData})

def delete_timetable_admin(request, id):
    timetable_coach = get_object_or_404(TimetableCoach, id=id)
    timetable_coach.delete()
    title = "Ваш клиент удалил запись"
    text = f"Запись с клиентом {timetable_coach.member.lastName} {timetable_coach.member.firstName} {timetable_coach.member.patronymic} на {timetable_coach.dateTime} удалена"
    send_email(
        title,
        timetable_coach.trainer.email,
        text
    )
    create_notification(timetable_coach.trainer.user, title, text)
    return redirect('recordTrainerTimeTable')

def delete_timetable_user(request, id):
    timetable_coach = get_object_or_404(TimetableCoach, id=id)
    timetable_coach.delete()
    title = "Ваш клиент удалил запись"
    text = f"Запись с клиентом {timetable_coach.member.lastName} {timetable_coach.member.firstName} {timetable_coach.member.patronymic} на {timetable_coach.dateTime} удалена"
    send_email(
        title,
        timetable_coach.trainer.email,
        text
    )
    create_notification(timetable_coach.trainer.user, title, text)
    return redirect('records')

def delete_timetable_coach(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    timetable_coach = get_object_or_404(TimetableCoach, id=id)
    timetable_coach.delete()
    title = "Ваша запись удалена"
    text = f"Запись с тренером {timetable_coach.trainer.lastName} {timetable_coach.trainer.firstName} {timetable_coach.trainer.patronymic} на {timetable_coach.dateTime} удалена"
    send_email(
        title,
        timetable_coach.member.email,
        text
    )
    create_notification(timetable_coach.member.user, title, text)
    return redirect('timeTable')


def add_room(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('workSite')  # замените на ваше URL
    else:
        form = RoomForm()
    return render(request, 'admin/function/Add/addRoom.html', {'form': form, 'admin': adminData})

# Редактирование
def edit_room(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    room = get_object_or_404(Room, id=id)
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            return redirect('workSite')
    else:
        form = RoomForm(instance=room)
    return render(request, 'admin/function/Add/addRoom.html', {'form': form, 'admin': adminData})

# Удаление
def delete_room(request, id):
    room = get_object_or_404(Room, id=id)
    room.delete()
    return redirect('workSite')

# Добавление новости
def add_news(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            title = "У нас свежие новости"
            text = "Ты можешь увидеть их на нашем сайте во вкладке новости."
            send_email(
                title,
                User.objects.all(),
                text
            )
            create_notification(User.objects.all(), title, text)
            return redirect('WorkTable')  # замените на ваше URL
    else:
        form = NewsForm()
    return render(request, 'admin/function/Add/addNews.html', {'form': form, 'admin': adminData})

# Редактирование новости
def edit_news(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    news_item = get_object_or_404(News, id=id)
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news_item)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = NewsForm(instance=news_item)
    return render(request, 'admin/function/Add/addNews.html', {'form': form, 'admin': adminData})

# Удаление новости
def delete_news(request, id):
    news_item = get_object_or_404(News, id=id)
    news_item.delete()
    return redirect('WorkTable')


# Добавление нового тренера
def coach_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = CoachForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            title = "У нас новый тренер"
            text = f"Тренер {form.lastName} {form.firstName} {form.patronymic} будет ждать вас на первую тренировку"
            send_email(
                title,
                User.objects.all(),
                text
            )
            create_notification(User.objects.all(), title, text)
            return redirect('WorkTable')
    else:
        form = CoachForm()
    return render(request, 'admin/function/Add/addTrainer.html', {'form': form, 'admin': adminData})

# Редактирование тренера
def coach_update(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    coach = get_object_or_404(Coach, id=id)
    if request.method == 'POST':
        form = CoachForm(request.POST, request.FILES, instance=coach)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = CoachForm(instance=coach)
    return render(request, 'admin/function/Add/addTrainer.html', {'form': form, 'admin': adminData})

# Удаление тренера
def coach_delete(request, id):
    coach = get_object_or_404(Coach, id=id)
    coach.delete()
    return redirect('WorkTable')

# Добавление новой подписки
def subscription_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            title = "У нас новый абонемент"
            text = f"У нас новый абонемент {form.title} опробуйте его возможности!"
            send_email(
                title,
                User.objects.all(),
                text
            )
            create_notification(User.objects.all(), title, text)
            return redirect('WorkTable')
    else:
        form = SubscriptionForm()
    return render(request, 'admin/function/Add/addSubscriptions.html', {'form': form, 'admin': adminData})

# Редактирование подписки
def subscription_update(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    subscription = get_object_or_404(Subscription, id=id)
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = SubscriptionForm(instance=subscription)
    return render(request, 'admin/function/Add/addSubscriptions.html', {'form': form, 'admin': adminData})

# Удаление подписки
def subscription_delete(request, id):
    subscription = get_object_or_404(Subscription, id=id)
    subscription.delete()
    return redirect('WorkTable')


# Добавление пользователя
def member_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = MemberForm()
    return render(request, 'admin/function/Add/addMember.html', {'form': form, 'admin': adminData})

# Редактирование пользователя
def member_update(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    member = get_object_or_404(Member, id=id)
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = MemberForm(instance=member)
    return render(request, 'admin/function/Add/addMember.html', {'form': form, 'admin': adminData})

# Удаление пользователя
def member_delete(request, id):
    member = get_object_or_404(Member, id=id)
    member.delete()
    return redirect('WorkTable')

def coachType_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = CoachTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = CoachTypeForm()
    return render(request, 'admin/function/Add/addTrainerType.html', {'form': form, 'admin': adminData})

def coachType_update(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    coachType = get_object_or_404(CoachType, id=id)
    if request.method == 'POST':
        form = CoachTypeForm(request.POST, instance=coachType)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = CoachTypeForm(instance=coachType)
    return render(request, 'admin/function/Add/addTrainerType.html', {'form': form, 'admin': adminData})

def coachType_delete(request, id):
    coachType = get_object_or_404(CoachType, id=id)
    coachType.delete()
    return redirect('WorkTable')


def education_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = EducationForm()
    return render(request, 'admin/function/Add/addEducation.html', {'form': form, 'admin': adminData})

def education_update(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    education = get_object_or_404(Education, id=id)
    if request.method == 'POST':
        form = EducationForm(request.POST, instance=education)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = EducationForm(instance=education)
    return render(request, 'admin/function/Add/addEducation.html', {'form': form, 'admin': adminData})

def education_delete(request, id):
    education = get_object_or_404(Education, id=id)
    education.delete()
    return redirect('WorkTable')

def direction_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = DirectionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = DirectionForm()
    return render(request, 'admin/function/Add/addEducation.html', {'form': form, 'admin': adminData})

def direction_update(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    direction = get_object_or_404(Direction, id=id)
    if request.method == 'POST':
        form = DirectionForm(request.POST, instance=direction)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = DirectionForm(instance=direction)
    return render(request, 'admin/function/Add/addEducation.html', {'form': form, 'admin': adminData})

def direction_delete(request, id):
    direction = get_object_or_404(Direction, id=id)
    direction.delete()
    return redirect('WorkTable')

def subscriptionCategory_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = SubscriptionCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = SubscriptionCategoryForm()
    return render(request, 'admin/function/Add/addTrainerType.html', {'form': form, 'admin': adminData})

def subscriptionCategory_update(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    subscriptionCategory = get_object_or_404(SubscriptionCategory, id=id)
    if request.method == 'POST':
        form = SubscriptionCategoryForm(request.POST, instance=subscriptionCategory)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = SubscriptionCategoryForm(instance=subscriptionCategory)
    return render(request, 'admin/function/Add/addTrainerType.html', {'form': form, 'admin': adminData})

def subscriptionCategory_delete(request, id):
    subscriptionCategory = get_object_or_404(SubscriptionCategory, id=id)
    subscriptionCategory.delete()
    return redirect('WorkTable')



def user_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = UserForm()
    return render(request, 'admin/function/Add/addUser.html', {'form': form, 'admin': adminData})

def user_update(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    user1 = get_object_or_404(User, id=id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user1)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = UserForm(instance=user1)
    return render(request, 'admin/function/Add/addUser.html', {'form': form, 'admin': adminData})

def user_delete(request, id):
    user = get_object_or_404(User, id=id)
    user.delete()
    return redirect('WorkTable')


def shopCategory_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = ShopCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = ShopCategoryForm()
    return render(request, 'admin/function/Add/addShopCategory.html', {'form': form, 'admin': adminData})

def shopCategory_update(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    shopCategory = get_object_or_404(ShopCategory, id=id)
    if request.method == 'POST':
        form = ShopCategoryForm(request.POST, instance=shopCategory)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = ShopCategoryForm(instance=shopCategory)
    return render(request, 'admin/function/Add/addShopCategory.html', {'form': form, 'admin': adminData})

def shopCategory_delete(request, id):
    shopCategory = get_object_or_404(ShopCategory, id=id)
    shopCategory.delete()
    return redirect('WorkTable')

def shopItem_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = ShopItemForm(request.POST)
        if form.is_valid():
            title = "У нас новый товар"
            text = f"У нас новый товар {form.title} опробуйте его возможности!"
            send_email(
                title,
                User.objects.all(),
                text
            )
            create_notification(User.objects.all(), title, text)
            form.save()
            return redirect('WorkTable')
    else:
        form = ShopItemForm()
    return render(request, 'admin/function/Add/addShopItem.html', {'form': form, 'admin': adminData})

def shopItem_update(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    shopItem = get_object_or_404(ShopItem, id=id)
    if request.method == 'POST':
        form = ShopItemForm(request.POST, instance=shopItem)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = ShopItemForm(instance=shopItem)
    return render(request, 'admin/function/Add/addShopItem.html', {'form': form, 'admin': adminData})

def shopItem_delete(request, id):
    shopItem = get_object_or_404(ShopItem, id=id)
    shopItem.delete()
    return redirect('WorkTable')


def personalCard_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = PersonalCardForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = PersonalCardForm()
    return render(request, 'admin/function/Add/AddPersCard.html', {'form': form, 'admin': adminData})

def personalCard_update(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    personalCard_update = get_object_or_404(PersonalCard, id=id)
    if request.method == 'POST':
        form = PersonalCardForm(request.POST, instance=personalCard_update)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = PersonalCardForm(instance=personalCard_update)
    return render(request, 'admin/function/Add/AddPersCard.html', {'form': form, 'admin': adminData})

def personalCard_delete(request, id):
    personalCard_update = get_object_or_404(PersonalCard, id=id)
    personalCard_update.delete()
    return redirect('WorkTable')


def subscriptionFeature_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = SubscriptionFeatureForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = SubscriptionFeatureForm()
    return render(request, 'admin/function/Add/addSubFeat.html', {'form': form, 'admin': adminData})

def subscriptionFeature_update(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        request.session.clear()
        return render(request, 'auth/login.html')

    user = User.objects.get(id=user_id)
    adminData = Administrator.objects.get(user_id=user.id)

    subscriptionFeature = get_object_or_404(SubscriptionFeature, id=id)
    if request.method == 'POST':
        form = SubscriptionFeatureForm(request.POST, instance=subscriptionFeature)
        if form.is_valid():
            form.save()
            return redirect('WorkTable')
    else:
        form = SubscriptionFeatureForm(instance=subscriptionFeature)
    return render(request, 'admin/function/Add/addSubFeat.html', {'form': form, 'admin': adminData})

def subscriptionFeature_delete(request, id):
    subscriptionFeature = get_object_or_404(SubscriptionFeature, id=id)
    subscriptionFeature.delete()
    return redirect('WorkTable')

def consl_delete(request, id):
    cons = get_object_or_404(Consultation, id=id)
    cons.delete()
    return redirect('workTable')

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from rest_framework import status




class CustomTokenObtainView(APIView):
    def post(self, request):
        serializer = CustomTokenObtainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = serializer.validated_data['user']
        user = User.objects.get(id=user_data['id'])

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user_data

        })

class GenericDeleteView(APIView):
    def delete(self, request, model_name, pk):
        try:
            model = apps.get_model('FitnessApp', model_name)
            model_name_str = model.__name__  # Получение названия модели
        except LookupError:
            return Response({"detail": "Model not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            obj = model.objects.get(pk=pk)
            obj.delete()
            return Response({"detail": f"{model_name_str} deleted."}, status=status.HTTP_204_NO_CONTENT)
        except model.DoesNotExist:
            return Response({"detail": "Object not found."}, status=status.HTTP_404_NOT_FOUND)


from rest_framework.parsers import MultiPartParser, FormParser


class GenericCreateImageView(APIView):
    def post(self, request, model_name):
        try:
            model = apps.get_model('FitnessApp', model_name)
            model_class_name = model.__name__
        except LookupError:
            return Response({"detail": "Model not found."}, status=status.HTTP_404_NOT_FOUND)

        # Извлечь JSON из поля 'data'
        data_json = request.data.get('data')
        print(data_json)
        if not data_json:
            return Response({"detail": "No data provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = json.loads(data_json)
        except json.JSONDecodeError:
            return Response({"detail": "Invalid JSON."}, status=status.HTTP_400_BAD_REQUEST)

        # Добавить файлы из request.FILES
        if request.FILES:
            for file_field in request.FILES:
                data[file_field] = request.FILES[file_field]

        # Обработка ForeignKey
        for field in model._meta.get_fields():
            if field.is_relation and not field.auto_created:
                field_name = field.name
                if field_name in data:
                    value = data[field_name]
                    if isinstance(value, dict) and 'id' in value:
                        data[f"{field_name}_id"] = value['id']
                        data.pop(field_name)
                    elif isinstance(value, (int, str)):
                        data[f"{field_name}_id"] = value
                        data.pop(field_name)

        try:
            obj = model.objects.create(**data)
            return Response({"detail": f"{model_class_name} created.", "id": obj.pk}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GenericCreateView(APIView):
    def post(self, request, model_name):
        try:
            model = apps.get_model('FitnessApp', model_name)
            model_class_name = model.__name__
        except LookupError:
            return Response({"detail": "Model not found."}, status=status.HTTP_404_NOT_FOUND)

        # Используем request.data напрямую
        data = request.data
        print(data)

        # Добавить файлы из request.FILES
        if request.FILES:
            for file_field in request.FILES:
                data[file_field] = request.FILES[file_field]

        # Обработка ForeignKey
        for field in model._meta.get_fields():
            if field.is_relation and not field.auto_created:
                field_name = field.name
                if field_name in data:
                    value = data[field_name]
                    if isinstance(value, dict) and 'id' in value:
                        data[f"{field_name}_id"] = value['id']
                        data.pop(field_name)
                    elif isinstance(value, (int, str)):
                        data[f"{field_name}_id"] = value
                        data.pop(field_name)

        # Создание объекта
        try:
            obj = model.objects.create(**data)
            return Response({"detail": f"{model_class_name} created.", "id": obj.pk}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GenericUpdateImageView(APIView):
    def put(self, request, model_name, pk):
        try:
            model = apps.get_model('FitnessApp', model_name)
            model_class_name = model.__name__
        except LookupError:
            return Response({"detail": "Model not found."}, status=status.HTTP_404_NOT_FOUND)

        # Получение объекта по pk
        try:
            instance = model.objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({"detail": "Object not found."}, status=status.HTTP_404_NOT_FOUND)

        # Извлечь JSON из поля 'data'
        data_json = request.data.get('data')
        if not data_json:
            return Response({"detail": "No data provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = json.loads(data_json)
        except json.JSONDecodeError:
            return Response({"detail": "Invalid JSON."}, status=status.HTTP_400_BAD_REQUEST)

        # Добавить файлы из request.FILES
        if request.FILES:
            for file_field in request.FILES:
                data[file_field] = request.FILES[file_field]

        # Обработка ForeignKey
        for field in model._meta.get_fields():
            if field.is_relation and not field.auto_created:
                field_name = field.name
                if field_name in data:
                    value = data[field_name]
                    if isinstance(value, dict) and 'id' in value:
                        data[f"{field_name}_id"] = value['id']
                        data.pop(field_name)
                    elif isinstance(value, (int, str)):
                        data[f"{field_name}_id"] = value
                        data.pop(field_name)

        # Обновление объекта
        try:
            for key, value in data.items():
                setattr(instance, key, value)
            instance.save()
            return Response({"detail": f"{model_class_name} updated.", "id": instance.pk})
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DynamicUpdateAPIView(APIView):
    def put(self, request, model_name, pk):
            # Обновление существующего объекта
            try:
                model = apps.get_model('FitnessApp', model_name)
                model_name_str = model.__name__
            except LookupError:
                return Response({"detail": "Model not found."}, status=status.HTTP_404_NOT_FOUND)

            # Получение объекта или 404
            obj = get_object_or_404(model, pk=pk)

            data = request.data.copy()
            print(data)
            # Обработка ForeignKey
            for field in model._meta.get_fields():
                if field.is_relation and not field.auto_created:
                    field_name = field.name
                    if field_name in data:
                        value = data[field_name]
                        if isinstance(value, dict) and 'id' in value:
                            data[f"{field_name}_id"] = value['id']
                            data.pop(field_name)
                        elif isinstance(value, (int, str)):
                            data[f"{field_name}_id"] = value
                            data.pop(field_name)

            # Обновление объекта
            for attr, value in data.items():
                setattr(obj, attr, value)
            try:
                obj.save()
                return Response({"detail": f"{model_name_str} with id {pk} updated."})
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ShopItemCreateViev(APIView):
    def post(self, request):
        data = request.data.copy()

        # Обработка категории, если она приходит как словарь
        category_data = data.get('category')
        if isinstance(category_data, dict):
            category_id = category_data.get('id')
            if category_id:
                data['category_id'] = category_id
            else:
                return Response({"error": "Category ID not found"}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(category_data, int):
            data['category_id'] = category_data
        # если category — это просто id, то ничего делать не нужно

        serializer = ShopItemSerializer(data=data)
        if serializer.is_valid():
            shop_item = serializer.save()
            return Response(ShopItemSerializer(shop_item).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ShopItemUpdateView(APIView):
    def put(self, request, pk):
        try:
            shop_item = ShopItem.objects.get(pk=pk)
        except ShopItem.DoesNotExist:
            return Response({"error": "Товар не найден."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()

        # Обработка категории, если она приходит как словарь
        category_data = data.get('category')
        if isinstance(category_data, dict):
            category_id = category_data.get('id')
            if category_id:
                data['category_id'] = category_id
            else:
                return Response({"error": "ID категории не найден."}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(category_data, int):
            data['category_id'] = category_data
        # иначе, если category — это просто id, то ничего делать не нужно

        serializer = ShopItemSerializer(shop_item, data=data, partial=True)
        if serializer.is_valid():
            shop_item = serializer.save()
            return Response(ShopItemSerializer(shop_item).data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RoleListView(generics.ListAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class AchievementListView(generics.ListAPIView):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer

class UserAchievementListView(generics.ListAPIView):
    queryset = UserAchievement.objects.all()
    serializer_class = UserAchievementSerializer

class SubscriptionListView(generics.ListAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

class MemberListView(generics.ListAPIView):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

class NotificationListView(generics.ListAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

class NewsListView(generics.ListAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer

class CoachTypeListView(generics.ListAPIView):
    queryset = CoachType.objects.all()
    serializer_class = CoachTypeSerializer

class CoachListView(generics.ListAPIView):
    queryset = Coach.objects.all()
    serializer_class = CoachSerializer

class ReviewListView(generics.ListAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

class EducationListView(generics.ListAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer

class DirectionListView(generics.ListAPIView):
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer

class RoomListView(generics.ListAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

class PreviewListView(generics.ListAPIView):
    queryset = Preview.objects.all()
    serializer_class = PreviewSerializer

class ShopCategoryListView(generics.ListAPIView):
    queryset = ShopCategory.objects.all()
    serializer_class = ShopCategorySerializer

class ShopItemListView(generics.ListAPIView):
    queryset = ShopItem.objects.all()
    serializer_class = ShopItemSerializer

class BasketListView(generics.ListAPIView):
    queryset = Basket.objects.all()
    serializer_class = BasketSerializer

class GetPreviewTagsListView(generics.ListAPIView):
    queryset = GetPreviewTags.objects.all()
    serializer_class = GetPreviewTagsSerializer

class ConsultationListView(generics.ListAPIView):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer

class TimetableCoachListView(generics.ListAPIView):
    queryset = TimetableCoach.objects.all()
    serializer_class = TimetableCoachSerializer

class TimetableCoachPaymentListView(generics.ListAPIView):
    queryset = TimetableCoachPayment.objects.all()
    serializer_class = TimetableCoachPaymentSerializer

class SubscriptionPaymentListView(generics.ListAPIView):
    queryset = SubscriptionPayment.objects.all()
    serializer_class = SubscriptionPaymentSerializer

class BuyItemListView(generics.ListAPIView):
    queryset = BuyItem.objects.all()
    serializer_class = BuyItemSerializer

class ShopPaymentListView(generics.ListAPIView):
    queryset = ShopPayment.objects.all()
    serializer_class = ShopPaymentSerializer

class BuySubscriptionListView(generics.ListAPIView):
    queryset = BuySubscription.objects.all()
    serializer_class = BuySubscriptionSerializer

class SubscriptionCategoryListView(generics.ListAPIView):
    queryset = SubscriptionCategory.objects.all()
    serializer_class = SubscriptionCategorySerializer

class AdminsListView(generics.ListAPIView):
    queryset = Administrator.objects.all()
    serializer_class = AdminSerializer

class VisitListView(generics.ListAPIView):
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer