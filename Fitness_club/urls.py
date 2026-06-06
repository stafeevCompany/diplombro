from django.contrib import admin
from rest_framework_simplejwt.views import TokenObtainPairView
from FitnessApp.views import *
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from FitnessApp.views import *

urlpatterns = [
    path('api/custom-token/', CustomTokenObtainView.as_view(), name='custom_token_obtain'),

    path('api/roles/', RoleListView.as_view(), name='role-list'),
    path('api/admins/', AdminsListView.as_view(), name='admin-list'),
    path('api/users/', UserListView.as_view(), name='user-list'),
    path('api/achievements/', AchievementListView.as_view(), name='achievement-list'),
    path('api/user-achievements/', UserAchievementListView.as_view(), name='user-achievement-list'),
    path('api/subscriptions/', SubscriptionListView.as_view(), name='subscription-list'),
    path('api/visits/', VisitListView.as_view(), name='subscription-list'),
    path('api/members/', MemberListView.as_view(), name='member-list'),
    path('api/notifications/', NotificationListView.as_view(), name='notification-list'),
    path('api/news/', NewsListView.as_view(), name='news-list'),
    path('api/coach-types/', CoachTypeListView.as_view(), name='coach-type-list'),
    path('api/coaches/', CoachListView.as_view(), name='coach-list'),
    path('api/reviews/', ReviewListView.as_view(), name='review-list'),
    path('api/educations/', EducationListView.as_view(), name='education-list'),
    path('api/directions/', DirectionListView.as_view(), name='direction-list'),
    path('api/rooms/', RoomListView.as_view(), name='room-list'),
    path('api/previews/', PreviewListView.as_view(), name='preview-list'),
    path('api/shop-categories/', ShopCategoryListView.as_view(), name='shop-category-list'),
    path('api/shop-items/', ShopItemListView.as_view(), name='shop-item-list'),
    path('api/baskets/', BasketListView.as_view(), name='basket-list'),
    path('api/preview-tags/', GetPreviewTagsListView.as_view(), name='get-preview-tags-list'),
    path('api/consultations/', ConsultationListView.as_view(), name='consultation-list'),
    path('api/timetables/', TimetableCoachListView.as_view(), name='timetable-coach-list'),
    path('api/timetable-payments/', TimetableCoachPaymentListView.as_view(),
                       name='timetable-coach-payment-list'),
    path('api/subscription-payments/', SubscriptionPaymentListView.as_view(),
                       name='subscription-payment-list'),
    path('api/subscription-category/', SubscriptionCategoryListView.as_view(),
                       name='subscription-category-list'),
    path('api/buy-items/', BuyItemListView.as_view(), name='buy-item-list'),
    path('api/shop-payments/', ShopPaymentListView.as_view(), name='shop-payment-list'),
    path('api/buy-subscriptions/', BuySubscriptionListView.as_view(), name='buy-subscription-list'),

    path('api/delete/<str:model_name>/<int:pk>/', GenericDeleteView.as_view(), name='generic-delete'),

    path('api/create/<str:model_name>/', GenericCreateView.as_view(), name='generic-create'),
    path('api/createImage/<str:model_name>/', GenericCreateImageView.as_view(), name='generic-create-iamge'),

    path('api/update/<str:model_name>/<int:pk>/', DynamicUpdateAPIView.as_view(), name='update_object'),
    path('api/updateImage/<str:model_name>/<int:pk>/', GenericUpdateImageView.as_view(), name='update_object_image'),

    #авторизация
    path("login/", login, name="login"),
    path("registration/", registration, name="registration"),
    path('admin/', admin.site.urls),

    #Админка
    path("adminMaimPage/", adminMainPage, name="adminMainPage"),
    path("achivmentsUser/", achivmentsUser, name="achivmentsUser"),
    path("achivmentsPage/<int:id>/", achivmentsPage, name="achivmentsPage"),

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
    path("records/", records, name="records"),
    path("", main_page, name="main_page"),

    # Функции пользователя
    path("buyRecord/<int:id>", buyRecord, name="buyRecord"),
    path("buySubscriptions/<int:id>", buySubscriptions, name="buySubscriptions"),
    path("buyItem/<int:id>", buyItem, name="buyItem"),


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



    #Добавление
    path('addVisit/', add_visit, name='add_visit'),
    path('addRecord/', add_record, name='add_record'),
    path('add_room/', add_room, name='add_room'),
    path('add_news/', add_news, name='add_news'),
    path('coach_create/', coach_create, name='coach_create'),
    path('subscription_create/', subscription_create, name='subscription_create'),
    path('member_create/', member_create, name='member_create'),
    path('coachType_create/', coachType_create, name='coachType_create'),
    path('education_create/', education_create, name='education_create'),
    path('direction_create/', direction_create, name='direction_create'),
    path('subscriptionCategory_create/', subscriptionCategory_create, name='subscriptionCategory_create'),
    path('user_create/', user_create, name='user_create'),
    path('shopCategory_create/', shopCategory_create, name='shopCategory_create'),
    path('shopItem_create/', shopItem_create, name='shopItem_create'),
    path('personalCard_create/', personalCard_create, name='personalCard_create'),
    path('subscriptionFeature_create/', subscriptionFeature_create, name='subscriptionFeature_create'),


    #Редактирование
    path('editVisit/<int:id>', edit_visit, name='edit_visit'),
    path('editRecord/<int:id>', edit_timetable_coach, name='edit_timetable_coach'),
    path('edit_room/<int:id>', edit_room, name='edit_room'),
    path('edit_news/<int:id>', edit_news, name='edit_news'),
    path('coach_update/<int:id>', coach_update, name='coach_update'),
    path('subscription_update/<int:id>', subscription_update, name='subscription_update'),
    path('member_update/<int:id>', member_update, name='member_update'),
    path('coachType_update/<int:id>', coachType_update, name='coachType_update'),
    path('education_update/<int:id>', education_update, name='education_update'),
    path('direction_update/<int:id>', direction_update, name='direction_update'),
    path('subscriptionCategory_update/<int:id>', subscriptionCategory_update, name='subscriptionCategory_update'),
    path('user_update/<int:id>', user_update, name='user_update'),
    path('shopCategory_update/<int:id>', shopCategory_update, name='shopCategory_update'),
    path('shopItem_update/<int:id>', shopItem_update, name='shopItem_update'),
    path('personalCard_update/<int:id>', personalCard_update, name='personalCard_update'),
    path('subscriptionFeature_update/<int:id>', subscriptionFeature_update, name='subscriptionFeature_update'),

    #Удаление
    path("deleteVisitAdmin/<int:id>", delete_timetable_admin, name="delete_timetable_admin"),
    path("deleteVisitUser/<int:id>", delete_timetable_user, name="delete_timetable_user"),
    path("deleteVisit/<int:id>", delete_visit, name="deleteVisit"),
    path("deleteRecord/<int:id>", delete_timetable_coach, name="delete_timetable_coach"),
    path("delete_room/<int:id>", delete_room, name="delete_room"),
    path("delete_news/<int:id>", delete_news, name="delete_news"),
    path("coach_delete/<int:id>", coach_delete, name="coach_delete"),
    path("subscription_delete/<int:id>", subscription_delete, name="subscription_delete"),
    path("member_delete/<int:id>", member_delete, name="member_delete"),
    path("coachType_delete/<int:id>", coachType_delete, name="coachType_delete"),
    path("education_delete/<int:id>", education_delete, name="education_delete"),
    path("direction_delete/<int:id>", direction_delete, name="direction_delete"),
    path("subscriptionCategory_delete/<int:id>", subscriptionCategory_delete, name="subscriptionCategory_delete"),
    path("user_delete/<int:id>", user_delete, name="user_delete"),
    path("shopCategory_delete/<int:id>", shopCategory_delete, name="shopCategory_delete"),
    path("shopItem_delete/<int:id>", shopItem_delete, name="shopItem_delete"),
    path("personalCard_delete/<int:id>", personalCard_delete, name="personalCard_delete"),
    path("subscriptionFeature_delete/<int:id>", subscriptionFeature_delete, name="subscriptionFeature_delete"),
    path("consl_delete/<int:id>", consl_delete, name="consl_delete"),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
