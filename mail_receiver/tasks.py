from celery import shared_task
from .views import fetch_emails
from django.http import HttpRequest
import logging

logger = logging.getLogger(__name__)

@shared_task
def fetch_emails_task():
    logger.info('Rozpoczynam zadanie fetch_emails_task')
    request = HttpRequest()
    result = fetch_emails(request)
    logger.info(f'Zakończono zadanie fetch_emails_task z wynikiem: {result.content}')