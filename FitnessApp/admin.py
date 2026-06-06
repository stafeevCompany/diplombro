from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(Consultation)
admin.site.register(Coach)
admin.site.register(CoachType)
admin.site.register(News)
admin.site.register(Notification)
admin.site.register(Member)
admin.site.register(Subscription)
admin.site.register(Role)
admin.site.register(Room)
admin.site.register(Preview)
admin.site.register(SubscriptionCategory)
admin.site.register(Education)
admin.site.register(Direction)
admin.site.register(SubscriptionFeature)
admin.site.register(BuySubscription)
admin.site.register(TimetableCoach)
admin.site.register(GetPreviewTags)
admin.site.register(Visit)
admin.site.register(SubscriptionPayment)

admin.site.register(TimetableCoachPayment)
admin.site.register(Administrator)

admin.site.register(ShopCategory)
admin.site.register(ShopItem)
admin.site.register(Basket)
admin.site.register(ShopPayment)
admin.site.register(Achievement)
admin.site.register(UserAchievement)
admin.site.register(BuyItem)
admin.site.register(Review)
# Register your models here.
class PersonalCardAdmin(admin.ModelAdmin):
    readonly_fields = ('qrCode',)  # Сделать поле только для чтения
    exclude = ('qrCode','code')            # Или полностью убрать из формы

admin.site.register(PersonalCard, PersonalCardAdmin)