from django.db import models


# 🧑 Merchant
class Merchant(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


# 💰 Ledger Entry (Credits & Debits)
class LedgerEntry(models.Model):
    ENTRY_TYPE = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )

    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    amount = models.BigIntegerField()  # paise
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.merchant.name} - {self.entry_type} - {self.amount}"


# 📤 Payout
class Payout(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    amount = models.BigIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    idempotency_key = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # 🔒 State machine validation
    def can_transition(self, new_status):
        valid_transitions = {
            'pending': ['processing'],
            'processing': ['completed', 'failed'],
            'completed': [],
            'failed': [],
        }
        return new_status in valid_transitions[self.status]

    def transition(self, new_status):
        if not self.can_transition(new_status):
            raise ValueError(f"Invalid transition from {self.status} to {new_status}")
        self.status = new_status
        self.save()

    def __str__(self):
        return f"Payout {self.id} - {self.status}"


# 🔑 Idempotency
class IdempotencyKey(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    key = models.CharField(max_length=255)
    response_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('merchant', 'key')
        indexes = [
            models.Index(fields=['merchant', 'key']),
        ]