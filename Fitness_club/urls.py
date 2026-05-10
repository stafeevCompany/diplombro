from django.contrib import admin
from FitnessApp.views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
urlpatterns = [
    #авторизация
    path("login/", login, name="login"),
    path("registration/", registration, name="registration"),
    path('admin/', admin.site.urls),

    #Админка
    path("adminMaimPage/", adminMainPage, name="adminMainPage"),

    #Таблицы для Админа
    path("WorkTable/", WorkTable, name="WorkTable"),
    path("workSite/", workSite, name="workSite"),
    path("timeTable/", timeTable, name="timeTable"),
    path("visitsTable/", visitsTable, name="visitsTable"),
    path("paymentsTable/", paymentsTable, name="paymentsTable"),

    #Для тренера
    path("mainTrainerPage/", mainTrainerPage, name="mainTrainerPage"),
    path("recordTrainerTimeTable/", recordTrainerTimeTable, name="recordTrainerTimeTable"),

    #Для пользователя
    path("profile_user/", profile_user, name="profile_user"),
    path("notification/", notification, name="notification"),

    path("page_trainer/<int:id>/", page_trainer, name="page_trainer"),
    path("pageItem/<int:id>", pageItem, name="pageItem"),
    path("page_new/<int:id>/", page_new, name="page_new"),
    path("timetable/", timetable, name="timetable"),
    path("records/", records, name="records"),
    path("", main_page, name="main_page"),

    # Функции пользователя
    path("buyRecord/<int:id>", buyRecord, name="buyRecord"),
    path("buySubscriptions/<int:id>", buySubscriptions, name="buySubscriptions"),
    path("buyItem/<int:id>", buyItem, name="buyItem"),

    path("deleteRecord/<int:id>/", main_page, name="deleteRecord"),

    path("editProfile/", editProfile, name="editProfile"),

    path('create_payment_subscription/<int:id>', create_payment_subscription, name='create_payment_subscription'),
    path('create_payment_recordTrainer/<int:id>', create_payment_recordTrainer,name='create_payment_recordTrainer'),
    path('create_payment_item/<int:id>', create_payment_item, name='create_payment_item'),

    #Каталоги
    path("news/", news, name="news"),
    path("trainers/", trainers, name="trainers"),
    path("subscriptions/", subscriptions, name="subscriptions"),
    path("shop/", shop, name="shop"),

    path("basket/", basket, name="basket"),
    path("deleteBasketItem/<int:id>", deleteItem, name="deleteBasketItem"),

    #Выход
    path('logout/', logout, name='logout'),



]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
