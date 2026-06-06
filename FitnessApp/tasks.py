from celery import shared_task
from datetime import timedelta
from .models import *  # модель с тренировками
from .utils import send_email
from .views import create_notification

import logging

logger = logging.getLogger(__name__)



@shared_task
def send_training_reminders():
    logger.info("Запуск задачи отправки напоминаний")
    now = timezone.now()
    upcoming_sessions = TimetableCoach.objects.filter(
        dateTime__gte=now,
        dateTime__lte=now + timedelta(hours=1)
    )
    logger.info(f"Найдено сессий: {upcoming_sessions.count()}")
    for session in upcoming_sessions:
        user_email = session.member.user # убедитесь, что у вас есть поле email
        title = f"Ваша тренировка начнется через час!"
        text = f"Ваш тренер {session.trainer.first_name} {session.trainer.last_name} будет ожидать вас в зале. Не опаздывайте!"

        send_email(
            title,
            session.member.email,
            text
        )
        create_notification(
            user=user_email, title=title, text=text
        )
        logger.info(f"Отправлено уведомление для {user_email}")