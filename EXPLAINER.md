# 📄 EXPLAINER.md

## 📌 Overview

This project is a mini payout engine built using Django. It simulates how real-world fintech systems handle balances, payouts, and transaction safety.

The system is designed with a focus on:

* Accurate balance management
* Prevention of duplicate transactions
* Concurrency safety
* Reliable payout processing

---

## 💰 Ledger-Based Design

Instead of storing balance directly, the system uses a **ledger-based approach**.

### Why?

* Prevents inconsistencies
* Maintains full transaction history
* Aligns with real-world financial systems

### How it works:

Each transaction is recorded as:

* `credit` → money added
* `debit` → money deducted

### Balance Calculation:

```
Balance = Total Credits - Total Debits
```

---

## 📤 Payout Flow

When a payout request is made:

1. Merchant is fetched from database
2. Idempotency key is validated
3. Balance is calculated
4. If sufficient balance:

   * A debit entry is created
   * A payout record is created (status = `pending`)
5. Response is returned

---

## 🔁 Idempotency

### Problem

Duplicate API requests (due to retries or network issues) can create multiple payouts.

### Solution

* Each request includes an `Idempotency-Key`
* The system stores the key and corresponding response
* If the same key is reused:

  * The stored response is returned
  * No new payout is created

### Additional Safety

* A database constraint (`unique_together`) ensures uniqueness at the DB level

---

## 🔒 Concurrency Handling

### Problem

Multiple simultaneous requests can lead to:

* Double spending
* Incorrect balances

### Solution

* `transaction.atomic()` ensures operations are executed as a single unit
* `select_for_update()` locks the merchant row during processing

This guarantees:

* Only one transaction updates balance at a time
* Race conditions are prevented

---

## 🔄 Payout State Machine

Each payout moves through defined states:

```
pending → processing → completed / failed
```

### Meaning:

* **pending** → payout created
* **processing** → worker is handling it
* **completed** → payout successful
* **failed** → payout failed (amount refunded)

---

## ⚙️ Background Processing

Payouts are processed asynchronously using a Django management command:

```
python manage.py process_payouts
```

### How it works:

1. Fetch all `pending` payouts
2. Mark them as `processing`
3. Simulate processing delay
4. Update status to:

   * `completed` OR
   * `failed` (with refund)

This simulates real-world background job processing.

---

## 🌐 API Design

### 1. Get Balance

* Endpoint: `/api/balance/<merchant_id>/`
* Method: GET
* Returns computed balance

---

### 2. Create Payout

* Endpoint: `/api/payout/<merchant_id>/`
* Method: POST
* Requires:

  * amount
  * `Idempotency-Key` header

---

### 3. Add Money (Demo)

* Endpoint: `/api/add-money/<merchant_id>/`
* Method: POST
* Adds credit to merchant

---

### 4. Payout Status

* Endpoint: `/api/payout-status/<payout_id>/`
* Method: GET
* Returns current payout status

---

## 🎨 Frontend

A simple HTML + JavaScript interface is provided to:

* View balance
* Add money
* Send payouts
* Track payout status in real-time

---

## ⚠️ Assumptions

* Single currency (₹ INR)
* Amount stored in **paise** to avoid floating-point errors
* Single merchant used for demonstration

---

## 🚀 Future Improvements

* Background processing with Celery
* Retry mechanism for failed payouts
* Authentication & multi-user support
* PostgreSQL for production
* Scalable job queue system

---

## 🎯 Conclusion

This project demonstrates:

* Real-world backend architecture
* Financial data integrity
* API reliability using idempotency
* Concurrency control using database locks
* Asynchronous processing design

The focus is on correctness, robustness, and system design rather than UI complexity.
