# payments/urls.py
from django.urls import path

from .views import CreateCheckoutView, MercadoPagoWebhookView

urlpatterns = [
    path("payments/checkout", CreateCheckoutView.as_view(), name="payments-checkout"),
    path("payments/mercadopago/webhook", MercadoPagoWebhookView.as_view(), name="mp-webhook"),
]
