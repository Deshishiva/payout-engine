from django.db.models import Sum
from .models import LedgerEntry


def get_balance(merchant):
    credits = LedgerEntry.objects.filter(
        merchant=merchant,
        entry_type='credit'
    ).aggregate(total=Sum('amount'))['total'] or 0

    debits = LedgerEntry.objects.filter(
        merchant=merchant,
        entry_type='debit'
    ).aggregate(total=Sum('amount'))['total'] or 0

    return credits - debits