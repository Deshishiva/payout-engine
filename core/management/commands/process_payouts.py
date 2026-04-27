from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Payout, LedgerEntry
import random
import time


class Command(BaseCommand):
    help = 'Process payouts'

    def handle(self, *args, **kwargs):
        payouts = Payout.objects.filter(status='pending')

        if not payouts.exists():
            self.stdout.write("No pending payouts")
            return

        for payout in payouts:

            # 🔒 Step 1: Mark as processing (with lock)
            with transaction.atomic():
                payout = Payout.objects.select_for_update().get(id=payout.id)

                if payout.status != 'pending':
                    continue

                payout.status = 'processing'
                payout.save()

            print(f"🔄 Payout {payout.id} → processing")

            # ⏳ IMPORTANT: delay so UI can show "processing"
            time.sleep(3)

            # 🎲 Random outcome
            outcome = random.choice(['completed', 'failed'])

            # 🔒 Step 2: Final state update
            with transaction.atomic():
                payout = Payout.objects.select_for_update().get(id=payout.id)

                if payout.status != 'processing':
                    continue

                if outcome == 'completed':
                    payout.status = 'completed'

                elif outcome == 'failed':
                    payout.status = 'failed'

                    # 💰 Refund money
                    LedgerEntry.objects.create(
                        merchant=payout.merchant,
                        amount=payout.amount,
                        entry_type='credit'
                    )

                payout.save()

            print(f"✅ Payout {payout.id} → {outcome}")

        self.stdout.write("🎉 Payout processing done")