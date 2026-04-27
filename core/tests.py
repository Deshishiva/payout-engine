from django.test import TestCase
from rest_framework.test import APIClient
from .models import Merchant, LedgerEntry, Payout


class PayoutTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Create merchant
        self.merchant = Merchant.objects.create(name="Test Merchant")

        # Add initial balance (₹1000 → 100000 paise)
        LedgerEntry.objects.create(
            merchant=self.merchant,
            amount=100000,
            entry_type='credit'
        )

    # ✅ Test balance API
    def test_get_balance(self):
        response = self.client.get(f"/api/balance/{self.merchant.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['balance'], 100000)

    # ✅ Test successful payout
    def test_create_payout_success(self):
        response = self.client.post(
            f"/api/payout/{self.merchant.id}/",
            {"amount": 50000},
            format='json',
            HTTP_IDEMPOTENCY_KEY="test123"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['amount'], 50000)

        # Check payout created
        self.assertEqual(Payout.objects.count(), 1)

    # ✅ Test insufficient balance
    def test_insufficient_balance(self):
        response = self.client.post(
            f"/api/payout/{self.merchant.id}/",
            {"amount": 200000},
            format='json',
            HTTP_IDEMPOTENCY_KEY="test124"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Insufficient balance", str(response.data))

    # ✅ Test idempotency (same key)
    def test_idempotency(self):
        response1 = self.client.post(
            f"/api/payout/{self.merchant.id}/",
            {"amount": 30000},
            format='json',
            HTTP_IDEMPOTENCY_KEY="same-key"
        )

        response2 = self.client.post(
            f"/api/payout/{self.merchant.id}/",
            {"amount": 30000},
            format='json',
            HTTP_IDEMPOTENCY_KEY="same-key"
        )

        # Should return same response
        self.assertEqual(response1.data, response2.data)

        # Only ONE payout created
        self.assertEqual(Payout.objects.count(), 1)

    # ✅ Test add money
    def test_add_money(self):
        response = self.client.post(
            f"/api/add-money/{self.merchant.id}/",
            {"amount": 50000},
            format='json'
        )

        self.assertEqual(response.status_code, 200)

        # Balance should increase
        balance_response = self.client.get(f"/api/balance/{self.merchant.id}/")
        self.assertEqual(balance_response.data['balance'], 150000)

    # ✅ Test payout status API
    def test_payout_status(self):
        response = self.client.post(
            f"/api/payout/{self.merchant.id}/",
            {"amount": 20000},
            format='json',
            HTTP_IDEMPOTENCY_KEY="status-test"
        )

        payout_id = response.data['payout_id']

        status_response = self.client.get(f"/api/payout-status/{payout_id}/")

        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.data['payout_id'], payout_id)