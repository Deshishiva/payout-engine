from django.db import transaction
from django.db.models import Sum
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Merchant, LedgerEntry, Payout, IdempotencyKey


# ✅ Frontend Home Page
def home(request):
    return render(request, 'index.html')


# ✅ Balance API
@api_view(['GET'])
def get_balance_view(request, merchant_id):
    try:
        merchant = Merchant.objects.get(id=merchant_id)
    except Merchant.DoesNotExist:
        return Response({"error": "Merchant not found"}, status=404)

    credits = LedgerEntry.objects.filter(
        merchant=merchant, entry_type='credit'
    ).aggregate(total=Sum('amount'))['total'] or 0

    debits = LedgerEntry.objects.filter(
        merchant=merchant, entry_type='debit'
    ).aggregate(total=Sum('amount'))['total'] or 0

    balance = credits - debits

    return Response({
        "merchant": merchant.name,
        "balance": balance
    })


# ✅ Create Payout API
@api_view(['POST'])
def create_payout(request, merchant_id):

    amount = int(request.data.get('amount', 0))
    idempotency_key = request.headers.get('Idempotency-Key')

    if not idempotency_key:
        return Response({"error": "Idempotency-Key required"}, status=400)

    with transaction.atomic():

        # 🔒 Lock merchant row
        try:
            merchant = Merchant.objects.select_for_update().get(id=merchant_id)
        except Merchant.DoesNotExist:
            return Response({"error": "Merchant not found"}, status=404)

        # 🔁 Idempotency check
        existing = IdempotencyKey.objects.filter(
            merchant=merchant,
            key=idempotency_key
        ).first()

        if existing:
            return Response(existing.response_data)

        # 💰 Calculate balance
        credits = LedgerEntry.objects.filter(
            merchant=merchant, entry_type='credit'
        ).aggregate(total=Sum('amount'))['total'] or 0

        debits = LedgerEntry.objects.filter(
            merchant=merchant, entry_type='debit'
        ).aggregate(total=Sum('amount'))['total'] or 0

        balance = credits - debits

        if balance < amount:
            return Response({"error": "Insufficient balance"}, status=400)

        # ➖ Deduct money
        LedgerEntry.objects.create(
            merchant=merchant,
            amount=amount,
            entry_type='debit'
        )

        # 📤 Create payout
        payout = Payout.objects.create(
            merchant=merchant,
            amount=amount,
            status='pending',
            idempotency_key=idempotency_key
        )

        response_data = {
            "payout_id": payout.id,
            "status": payout.status,
            "amount": payout.amount
        }

        # 🔁 Save idempotency
        IdempotencyKey.objects.create(
            merchant=merchant,
            key=idempotency_key,
            response_data=response_data
        )

        return Response(response_data)


# ✅ Add Money API
@api_view(['POST'])
def add_credit(request, merchant_id):
    try:
        merchant = Merchant.objects.get(id=merchant_id)
    except Merchant.DoesNotExist:
        return Response({"error": "Merchant not found"}, status=404)

    amount = int(request.data.get('amount', 0))

    if amount <= 0:
        return Response({"error": "Invalid amount"}, status=400)

    LedgerEntry.objects.create(
        merchant=merchant,
        amount=amount,
        entry_type='credit'
    )

    return Response({
        "message": "Money added successfully",
        "amount": amount
    })


# ✅ Get Payout Status API (NEW 🚀)
@api_view(['GET'])
def get_payout(request, payout_id):
    try:
        payout = Payout.objects.get(id=payout_id)
    except Payout.DoesNotExist:
        return Response({"error": "Payout not found"}, status=404)

    return Response({
        "payout_id": payout.id,
        "status": payout.status,
        "amount": payout.amount
    })