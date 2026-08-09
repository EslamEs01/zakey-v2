"""Enforce ``Σ completed refunds ≤ captured`` in the database (FR-075, INV-004).

FR-075 requires the cap to be held by "a database constraint **plus** a locked
service check". The service check exists and is good, but it is not the
authority: anything that writes a ``Refund`` row without going through
``payments.services.refund`` — an import, a shell session, a repaired migration,
a future admin action, ``bulk_create`` — bypasses it entirely. The invariant that
decides whether ZAKEY pays a customer twice cannot live only in application code
while ``reserved <= on_hand`` lives in the schema.

A plain ``CheckConstraint`` cannot express this: the bound is an **aggregate over
sibling rows** compared against a column on the parent, and a ``CHECK`` sees only
the row in front of it. So the mechanism is a ``CONSTRAINT TRIGGER``.

**The lock is the load-bearing part.** Under ``READ COMMITTED``, two concurrent
transactions inserting refunds cannot see each other's uncommitted rows, so both
would compute the same stale sum and both would pass. The trigger therefore takes
``SELECT ... FOR UPDATE`` on the parent payment *before* summing, which serialises
them: the second transaction blocks until the first commits, then re-reads and
sees the money already returned. That makes the database — not the service — the
thing that cannot be raced.
"""

from django.db import migrations

FORWARD = """
CREATE OR REPLACE FUNCTION zakey_refund_cap_check() RETURNS trigger AS $$
DECLARE
    captured numeric(12, 2);
    refunded numeric(12, 2);
BEGIN
    -- Serialise concurrent refunds against the same payment. Without this the
    -- two transactions below each read a sum that excludes the other's
    -- uncommitted row, and both pass a bound neither of them actually meets.
    SELECT CASE
               WHEN p.state IN ('captured', 'partially_refunded', 'refunded')
                   THEN p.amount
               ELSE 0
           END
      INTO captured
      FROM payments_payment p
     WHERE p.id = NEW.payment_id
       FOR UPDATE;

    IF captured IS NULL THEN
        RAISE EXCEPTION 'refund_cap: payment % does not exist', NEW.payment_id
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    SELECT COALESCE(SUM(r.amount), 0)
      INTO refunded
      FROM payments_refund r
     WHERE r.payment_id = NEW.payment_id
       AND r.state = 'completed';

    IF refunded > captured THEN
        RAISE EXCEPTION
            'refund_cap_exceeded: payment % would have % refunded against % captured',
            NEW.payment_id, refunded, captured
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- AFTER, so the row being judged is already visible to the SUM above.
-- DEFERRABLE INITIALLY IMMEDIATE: checked per statement by default, but a
-- deliberate bulk correction can defer it to the end of its transaction.
CREATE CONSTRAINT TRIGGER refund_never_exceeds_capture
    AFTER INSERT OR UPDATE ON payments_refund
    DEFERRABLE INITIALLY IMMEDIATE
    FOR EACH ROW EXECUTE FUNCTION zakey_refund_cap_check();
"""

REVERSE = """
DROP TRIGGER IF EXISTS refund_never_exceeds_capture ON payments_refund;
DROP FUNCTION IF EXISTS zakey_refund_cap_check();
"""


class Migration(migrations.Migration):
    dependencies = [("payments", "0001_initial")]

    operations = [migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE)]
