# Permissions Matrix

**Feature**: 004-zakey-commerce-backend-admin
Implements FR-110 – FR-115, INV-010.

Roles are Django `Group`s created by `python manage.py setup_roles` (idempotent). Permissions are enforced **server-side** in three places — queryset filtering, `has_view/add/change/delete_permission`, and action handlers. Hiding a Jazzmin menu link is presentation only and is **never** the enforcement mechanism (FR-111).

Legend: **V** view · **A** add · **C** change · **D** delete/archive · **X** execute action · **—** no access

---

## 1. Roles

| Role | Purpose |
|---|---|
| **Super Administrator** | Full technical control; the only role that manages staff accounts and permissions |
| **Store Manager** | Day-to-day commercial operation across catalogue, orders, inventory, promotions |
| **Catalogue Manager** | Products, categories, collections, media |
| **Inventory Manager** | Stock levels, adjustments, movement history |
| **Order Fulfilment** | Pick, pack, ship; no pricing, no refunds |
| **Customer Service** | Read orders and customers; add notes; limited cancellation |
| **Finance** | Payments, refunds, financial reporting |
| **Content Manager** | Storefront content, FAQs, static pages, SEO |
| **Read-only Auditor** | Read everything, change nothing, including audit log |

---

## 2. Matrix

| Model | Super | Store Mgr | Catalogue | Inventory | Fulfilment | Cust. Svc | Finance | Content | Auditor |
|---|---|---|---|---|---|---|---|---|---|
| **Catalogue** |
| Product | VACD | VACD | VACD | V | V | V | V | V | V |
| ProductVariant (incl. price) | VACD | VACD | VACD | V | V | V | V | — | V |
| ProductImage / Document | VACD | VACD | VACD | — | — | — | — | V | V |
| Category / Collection | VACD | VACD | VACD | V | V | V | — | V | V |
| Brand | VACD | VACD | VACD | — | — | — | — | V | V |
| **Inventory** |
| StockItem | VACD | VAC | V | VAC | V | V | V | — | V |
| StockMovement *(append-only)* | V | V | V | VA | V | — | V | — | V |
| StockReservation | V | V | — | V | V | V | — | — | V |
| **Orders** |
| Order | VACD | VAC | — | V | VC | VC | VC | — | V |
| OrderLine *(read-only)* | V | V | — | V | V | V | V | — | V |
| OrderAddress | V | VC | — | — | VC | VC | V | — | V |
| OrderEvent *(append-only)* | V | V | — | V | V | V | V | — | V |
| OrderNote | VACD | VAC | — | — | VA | VA | VA | — | V |
| **Payments** |
| PaymentMethod | VACD | VAC | — | — | — | — | VAC | — | V |
| Payment | VAC | VAC | — | — | — | V | VAC | — | V |
| PaymentEvent *(append-only)* | V | V | — | — | — | — | V | — | V |
| Refund | VAC | VA | — | — | — | — | VAC | — | V |
| **Customers** |
| User (customers) | VACD | VAC | — | — | V | VAC | V | — | V |
| CustomerProfile | VACD | VAC | — | — | V¹ | VAC | V¹ | — | V¹ |
| Address | VACD | VAC | — | — | V | VAC | — | — | V¹ |
| **Shipping** |
| Governorate / ServiceArea | VACD | VAC | — | — | V | V | — | — | V |
| ShippingZone / Method / Rate | VACD | VACD | — | — | V | V | V | — | V |
| InstallationService | VACD | VACD | — | — | V | V | V | — | V |
| **Promotions** |
| Coupon | VACD | VACD | VAC | — | — | V | V | — | V |
| CouponRedemption *(read-only)* | V | V | — | — | — | V | V | — | V |
| **Reviews** |
| Review | VACD | VACD | VAC | — | — | VAC | — | VAC | V |
| **Content** |
| SiteSetting | VAC | VAC | — | — | — | — | — | VAC | V |
| HomeSection / Banner / Partner | VACD | VAC | — | — | — | — | — | VACD | V |
| FAQ / StaticPage / Navigation | VACD | VAC | — | — | — | — | — | VACD | V |
| NewsletterSubscription | VACD | V | — | — | — | V | — | VAC | V |
| ContactMessage | VACD | V | — | — | — | VAC | — | VAC | V |
| **Staff & audit** |
| Staff User / Group | VACD | — | — | — | — | — | — | — | V |
| AuditLog *(immutable)* | V | V | — | — | — | — | V | — | V |

¹ **Redacted view** — phone and email are masked (`010****5678`); full values require `accounts.view_full_contact`.

---

## 3. Executable actions

| Action | Roles | Guard |
|---|---|---|
| Confirm order | Super, Store Mgr, Fulfilment | valid transition |
| Mark processing / shipped / delivered | Super, Store Mgr, Fulfilment | valid transition |
| Cancel order | Super, Store Mgr, Cust. Svc | only before `shipped` |
| Record payment | Super, Store Mgr, Finance | order not cancelled |
| Issue refund | Super, Finance | `Σ refunds ≤ captured` (INV-004) |
| Adjust stock | Super, Store Mgr, Inventory | reason required; `on_hand ≥ reserved` |
| Restock returned goods | Super, Store Mgr, Inventory | explicit decision (FR-028) |
| Publish / archive product | Super, Store Mgr, Catalogue | archive blocked→forced if ordered |
| Approve / reject review | Super, Store Mgr, Catalogue, Cust. Svc, Content | — |
| Activate / deactivate coupon | Super, Store Mgr, Catalogue | — |
| Export CSV | Super, Store Mgr, Finance, Auditor | financial columns need Finance |
| Manage staff & permissions | Super only | — |
| Run `seed_demo` | Super only, non-production | refuses when orders exist |

---

## 4. Hard rules

1. **Nobody**, including Super Administrator, can update or delete `AuditLog`, `StockMovement`, `PaymentEvent` or `OrderEvent` (FR-114, INV-013). There is no code path — not an admin permission, an absent implementation.
2. **Nobody** can edit `OrderLine` price, quantity or snapshot fields after creation (INV-003). Corrections are made by cancelling and re-creating, or by a refund.
3. `Order.grand_total` and its components are read-only in the admin; they change only through validated services.
4. `is_staff` and `is_superuser` are settable only by Super Administrator, and never from any storefront view (FR-057).
5. Customer-facing views filter every queryset by `request.user`; a miss returns **404, not 403** — 403 confirms the object exists (INV-010, FR-056).
6. Every permission change writes an `AuditLog` entry.
7. Read-only Auditor holds no `add`, `change` or `delete` permission on any model.

---

## 5. Verification

`tests/admin/test_permissions_matrix.py` is parametrised over **every (role × model × operation) cell** in §2 and asserts allow/deny by calling the admin view as that user — not by inspecting the permission table. `tests/admin/test_actions_permissions.py` does the same for §3. Together they satisfy SC-006.

A separate test asserts that Jazzmin menu visibility never grants access: it hides the menu for a role and confirms the URL is still refused.
