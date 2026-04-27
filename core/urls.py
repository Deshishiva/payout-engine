from django.urls import path
from .views import get_balance_view, create_payout, add_credit, get_payout

urlpatterns = [
    path('balance/<int:merchant_id>/', get_balance_view),
    path('payout/<int:merchant_id>/', create_payout),
    path('add-money/<int:merchant_id>/', add_credit),
    path('payout-status/<int:payout_id>/', get_payout),
]