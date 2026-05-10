from itertools import product

from dateutil.relativedelta import relativedelta
from django.db.models import Count, Q
from django.shortcuts import *

import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from FitnessApp.models import *
from .forms import LoginForm, RegistrationForm, QuantityForm
import json
from datetime import timedelta, datetime

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from collections import defaultdict
from django.utils import timezone

now = timezone.now()


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

                    user.is_active = True
                    user.save()
                    # Записываем данные пользователя в сессию
                    request.session['user_id'] = user.id
                    request.session['phone'] = user.phone
                    request.session['role'] = user.role.name
                    request.session['active'] = user.is_active


                    if user.role.name == "Администратор":
                        return redirect('adminMainPage')
                    elif user.role.name == "Тренер":
                        return redirect('mainTrainerPage')
                    elif user.role.name == "Пользователь":
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


            new_user =User.objects.create(
                    password=password,
                    phone=login,
                    is_active = False,
            )

            Member.objects.create(
                user=new_user,
                last_name=lastname,
                first_name=firstname,
                patronymic=patronymic,
                date_of_birth=birthday,
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
                payment_date__gte=first_day_of_month,
                payment_date__lt=next_month,
                is_successful=True,
                coach=trainerData
            )

            # Суммирование суммы
            total_earnings = float(monthly_payments.aggregate(total=Sum('amount_paid'))['total']) *0.6 or 0

            trainings_this_month = TimetableCoach.objects.filter(
                trainer=trainerData,
                dateTime__gte=first_day_of_month,
                dateTime__lt=next_month
            ).count()

            visitsTopMembers = TimetableCoach.objects.all().order_by('dateTime').distinct().first()
            # Получить участников, у которых есть тренировки с данным тренером, и отсортировать по количеству
            visits_often_members = Member.objects.annotate(
                training_count=Count('training_payments', filter=Q(training_payments__coach=trainerData))
            ).filter(
                training_count__gt=0
            ).order_by('-training_count')


            context = {
                "visits_json": visits_json,
                
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
        visitsTopMembers = Visit.objects.all().order_by('-visitDate').distinct().first()
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
                .filter(status=TimetableCoachPayment.Status.SUCCEEDED)
                .annotate(month=TruncMonth('created_at'))
                .values('month')
                .annotate(total=Sum('amount'))
                .order_by('month')
            )

            # Платежи по подпискам
            subscription_payments = (
                SubscriptionPayment.objects
                .filter(status=SubscriptionPayment.Status.SUCCEEDED)
                .annotate(month=TruncMonth('created_at'))
                .values('month')
                .annotate(total=Sum('amount'))
                .order_by('month')
            )

            monthly_totals = {}
            for month in all_months:
                # Используем форматирование, чтобы сравнивать одинаково
                monthly_totals[month.strftime('%Y-%m')] = {'training': 0, 'subscription': 0}

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


            # Формируем данные для графика
            dps1 = []
            for month in all_months:
                label = month.strftime('%B %Y')
                month_str = month.strftime('%Y-%m')
                total = (monthly_totals[month_str]['training'] +
                         monthly_totals[month_str]['subscription'])
                dps1.append({'label': label, 'y': total})

            adminData = Administrator.objects.get(user_id=user.id)
            subscription_payments = SubscriptionPayment.objects.all().filter(created_at__gte=start_month)
            training_payments = TimetableCoachPayment.objects.all().filter(created_at__gte=start_month)

            total_subscription_payment = sum(sp.amount for sp in subscription_payments)
            total_training_payment = sum(tp.amount for tp in training_payments)
            money = total_subscription_payment + total_training_payment

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
                "money": money,
                "visitsOftenMember": visits_often_members,
                "topVisitsOftenMember":visitsTopMembers
            }
            print("Данные для графика (dps1):", dps1)
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
            context = {
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
        subscriptionPayments = SubscriptionPayment.objects.all()
        if user:
            adminData = Administrator.objects.get(user_id=user.id)
            context = {
                "admin": adminData,
                'user': user,
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

def timeTable(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        timeTable = TimetableCoach.objects.all()

        if user:
            adminData = Administrator.objects.get(user_id=user.id)
            context = {
                "admin": adminData,
                'user': user,
                "timeTable": timeTable,
            }
            return render(request, 'admin/page/timeTable.html', context)
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
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            member = Member.objects.get(user_id=user.id)
            notifications = Notification.objects.filter(user_id=user_id).order_by("created_at")
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
            context = {
                "direction": direction,
                "trainer": trainer,
                "education": education,
                'user': user,

            }
            return render(request, 'trainer/../page/pageTrainer.html', context)
    else:
        request.session.clear()
        return render(request, 'trainer/../page/pageTrainer.html')

def page_new(request,id):
    user_id = request.session.get('user_id')
    new = get_object_or_404(News, id=id)
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            context = {
                "new": new,
                'user': user,

            }
            return render(request, 'trainer/../page/pageNews.html', context)
    else:
        request.session.clear()
        return render(request, 'trainer/../page/pageNews.html')

def timetable(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            context = {

                'user': user,

            }
            return render(request, 'trainer/timetable.html', context)
    else:
        request.session.clear()
        return render(request, 'trainer/timetable.html')


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
        member = Member.objects.get(user_id=user_id)
        card = PersonalCard.objects.get(member_id=member.id)
        if user:
            try:
                activeSubscription = BuySubscription.objects.get(personal_card_id=card.id)
                maxVisits = (activeSubscription.end_date - activeSubscription.start_date).days
                visits = Visit.objects.all().filter(
                    personal_card_id=card.id,
                    visitDate__gte=activeSubscription.start_date,
                    visitDate__lte=activeSubscription.end_date
                ).count()
                remainingVisits = visits
            except BuySubscription.DoesNotExist:
                activeSubscription = None
                maxVisits = None
                remainingVisits = None
            buySubscriptions =BuySubscription.objects.all().filter(personal_card_id=card.id)


            context = {
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
        return render(request, 'auth/login.html')


def editProfile(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        member = Member.objects.get(user_id=user_id)
        if user:
            context = {
                "member": member,
                'user': user,

            }
            return render(request, 'user/function/editProfile.html', context)
    else:
        request.session.clear()
        return render(request, 'auth/login.html')



def records(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        member = Member.objects.get(user_id=user.id)
        records = TimetableCoach.objects.all().filter(member_id=member.id).order_by('-dateTime')
        recordsPaid = TimetableCoach.objects.all().filter(member_id=member.id, status="Оплачено").order_by('-dateTime')
        recordsUnpaid = TimetableCoach.objects.all().filter(member_id=member.id, status="Не оплачено" ).order_by('-dateTime')

        # Общее количество записей для данного члена
        total_records = TimetableCoach.objects.filter(member_id=member.id).count()
        # Количество оплаченных
        paid_records_count = TimetableCoach.objects.filter(member_id=member.id, status='Оплачено').count()
        # Количество неоплаченных
        unpaid_records_count = TimetableCoach.objects.filter(member_id=member.id, status='Не оплачено').count()
        if user:
                context = {
                    "member": member,
                    'user': user,
                    'records': records,
                    'recordsPaid': recordsPaid,
                    'recordsUnpaid': recordsUnpaid,

                    'recordsCount': total_records,
                    'recordsPaidCount': paid_records_count,
                    'recordsUnpaidCount': unpaid_records_count,

                }
                return render(request, 'user/records.html', context)
        else:
            request.session.clear()
            return render(request, 'auth/login.html')

#Выход из сессии
def logout(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        if user:
            user.is_active = False
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
    try:
        order = get_object_or_404(Subscription, id=id)

        # Сумма в минимальных единицах валюты (например, центы для USD)
        # Убедитесь, что Decimal конвертируется правильно (умножаем на 100 для центов)
        # Создаем PaymentIntent в Stripe
        intent = stripe.PaymentIntent.create(
            amount=order.price,
            currency='rub', # Указывайте валюту заказа
            metadata={'order_id': order.id}, # Полезные метаданные
            # automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'}, # Опционально
        )

        # Создаем запись о платеже в нашей БД со статусом pending
        # Используем ID Intent'а как payment_id
        payment = SubscriptionPayment.objects.create(
            subscription=order,
            payment_id=intent.id,
            amount=order.price,
            currency='RUB', # Указывайте валюту заказа
            status=SubscriptionPayment.Status.PENDING
        )

        return JsonResponse({
            'clientSecret': intent.client_secret,
            'paymentId': payment.payment_id,
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
    try:
        order = get_object_or_404(TimetableCoach, id=id)

        # Сумма в минимальных единицах валюты (например, центы для USD)
        # Убедитесь, что Decimal конвертируется правильно (умножаем на 100 для центов)
        # Создаем PaymentIntent в Stripe
        intent = stripe.PaymentIntent.create(

            amount=order.trainer.price,
            currency='rub', # Указывайте валюту заказа
            metadata={'order_id': order.id}, # Полезные метаданные
            # automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'}, # Опционально
        )

        # Создаем запись о платеже в нашей БД со статусом pending
        # Используем ID Intent'а как payment_id
        paymentRecord = TimetableCoachPayment.objects.create(
            timetable_coach = order,
            payment_id=intent.id,
            amount = order.trainer.price,
            currency='RUB', # Указывайте валюту заказа
            status=TimetableCoachPayment.Status.PENDING,
        )

        return JsonResponse({
            'clientSecret': intent.client_secret,
            'paymentId': paymentRecord.payment_id,
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
    try:
        item = get_object_or_404(Basket, id=id)

        # Сумма в минимальных единицах валюты (например, центы для USD)
        # Убедитесь, что Decimal конвертируется правильно (умножаем на 100 для центов)
        # Создаем PaymentIntent в Stripe
        intent = stripe.PaymentIntent.create(
            amount=int(item.price),
            currency='rub', # Указывайте валюту заказа
            metadata={'order_id': item.id}, # Полезные метаданные
            # automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'}, # Опционально
        )

        # Создаем запись о платеже в нашей БД со статусом pending
        # Используем ID Intent'а как payment_id
        payment = ShopPayment.objects.create(
            item=item.item,
            payment_id=intent.id,
            quantity=item.quantity,
            amount=float(item.price),
            currency='RUB', # Указывайте валюту заказа
            status=SubscriptionPayment.Status.PENDING
        )

        item.delete()


        return JsonResponse({
            'clientSecret': intent.client_secret,
            'paymentId': payment.payment_id,
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

