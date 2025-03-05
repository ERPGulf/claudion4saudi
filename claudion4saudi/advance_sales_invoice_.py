import erpnext
from erpnext.accounts.doctype.journal_entry.journal_entry import get_exchange_rate
from erpnext.accounts.doctype.payment_entry.payment_entry import allocate_open_payment_requests_to_references, apply_early_payment_discount, get_bank_cash_account, get_outstanding_on_journal_entry, set_paid_amount_and_received_amount, set_party_account, set_party_account_currency
from erpnext.accounts.party import get_party_account, get_party_bank_account
import frappe
from frappe.utils import flt, getdate, nowdate


@frappe.whitelist()
def get_payment_entry(
    dn=None,  
    party_amount=None,
    bank_account=None,
    bank_amount=None,
    party_type=None,
    payment_type=None,
    reference_date=None,
    ignore_permissions=False,
    created_from_payment_request=False,
):
    dt = "Sales Order" 

    frappe.logger().info(f"Received params: dn={dn}, args={frappe.form_dict}")

    if not dn:
        dn = frappe.form_dict.get("sales_order")

    if not dn:
        frappe.throw(("Missing required parameter: dn (Sales Order name)"), title=("Validation Error"))

    try:
        doc = frappe.get_doc(dt, dn)
    except frappe.DoesNotExistError:
        frappe.throw(("Sales Order {0} not found").format(dn), title=("Error"))

    over_billing_allowance = frappe.db.get_single_value("Accounts Settings", "over_billing_allowance")
    if flt(doc.per_billed, 2) >= (100.0 + over_billing_allowance):
        frappe.throw(("Can only make payment against unbilled Sales Order"))

    if not party_type:
        party_type = "Customer"  

    party_account = set_party_account(dt, dn, doc, party_type)
    party_account_currency = set_party_account_currency(dt, party_account, doc)

    if not payment_type:
        payment_type = "Receive"  
    grand_total = flt(doc.grand_total)
    outstanding_amount = grand_total - flt(doc.advance_paid)

    bank = get_bank_cash_account(doc, bank_account)

    if not bank:
        party_bank_account = get_party_bank_account(party_type, doc.get("customer"))
        if party_bank_account:
            account = frappe.db.get_value("Bank Account", party_bank_account, "account")
            bank = get_bank_cash_account(doc, account)

    paid_amount, received_amount = set_paid_amount_and_received_amount(
        dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc
    )

    reference_date = getdate(reference_date)
    paid_amount, received_amount, discount_amount, valid_discounts = apply_early_payment_discount(
        paid_amount, received_amount, doc, party_account_currency, reference_date
    )

    financial_details = get_reference_details_(
        reference_doctype=dt,
        reference_name=dn,
        party_account_currency=party_account_currency,
        party_type=party_type,
        party=doc.get("customer")
    )

    pe = frappe.new_doc("Advance Sales Invoice")
    pe.payment_type = payment_type
    pe.company = doc.company
    pe.cost_center = doc.get("cost_center")
    pe.posting_date = nowdate()
    pe.reference_date = reference_date
    pe.mode_of_payment = doc.get("mode_of_payment")
    pe.party_type = party_type
    pe.party = doc.get("customer")
    pe.contact_person = doc.get("contact_person")
    pe.contact_email = doc.get("contact_email")

    if hasattr(pe, "ensure_supplier_is_not_blocked"):
        pe.ensure_supplier_is_not_blocked()

    pe.paid_from = party_account if payment_type == "Receive" else bank.account
    pe.paid_to = party_account if payment_type == "Pay" else bank.account
    pe.paid_from_account_currency = (
        party_account_currency if payment_type == "Receive" else bank.account_currency
    )
    pe.paid_to_account_currency = party_account_currency if payment_type == "Pay" else bank.account_currency
    pe.paid_amount = paid_amount
    pe.received_amount = received_amount
    pe.letter_head = doc.get("letter_head")
    pe.bank_account = frappe.db.get_value("Bank Account", {"is_company_account": 1, "is_default": 1}, "name")

    pe.project = doc.get("project") or next(
        (x.get("project") for x in doc.get("items") if x.get("project")), None
    )

    bank_account = get_party_bank_account(pe.party_type, pe.party)
    pe.set("party_bank_account", bank_account)
    pe.set_bank_account_data()

    if not pe.get("references"):
        pe.set("references", [])

    existing_references = {ref.reference_name for ref in pe.references}

    if dn not in existing_references:
        pe.append("references", {
        "reference_doctype": dt,
        "reference_name": dn,
        "total_amount": financial_details.get("total_amount"),
        "outstanding_amount": financial_details.get("outstanding_amount"),
        "exchange_rate": financial_details.get("exchange_rate"),
        "allocated_amount": paid_amount,
        "bill_no": financial_details.get("bill_no"),
        "due_date": financial_details.get("due_date"),
        "account_type": financial_details.get("account_type"),
        "payment_type": financial_details.get("payment_type"),
    })

    pe.run_method("set_missing_values") 
    pe.flags.ignore_validate = True

    if not pe.get("custom_item"):
        pe.set("custom_item", [])

    for item in doc.items:
        pe.append("custom_item", {
            "item_code": item.item_code,
            "delivery_date": item.delivery_date,
            "qty": item.qty,
            "rate": item.rate,
            "amount": item.amount,
            "actual_qty": item.actual_qty,
        })

    pe.unallocated_amount = max(0, paid_amount - grand_total)

    if party_account and bank:
        pe.db_set("company_currency", frappe.get_cached_value("Company", pe.company, "default_currency"))

        pe.set_exchange_rate(ref_doc=doc)
        pe.set_amounts()

    if not created_from_payment_request:
        allocate_open_payment_requests_to_references(pe.references, pe.precision("paid_amount"))

    return pe

@frappe.whitelist()
def get_reference_details_(
	reference_doctype, reference_name, party_account_currency, party_type=None, party=None
):
	total_amount = outstanding_amount = exchange_rate = account = None

	ref_doc = frappe.get_doc(reference_doctype, reference_name)
	company_currency = ref_doc.get("company_currency") or erpnext.get_company_currency(ref_doc.company)

	account_type = None
	payment_type = None

	if reference_doctype == "Dunning":
		total_amount = outstanding_amount = ref_doc.get("dunning_amount")
		exchange_rate = 1

	elif reference_doctype == "Journal Entry" and ref_doc.docstatus == 1:
		if ref_doc.multi_currency:
			exchange_rate = get_exchange_rate(party_account_currency, company_currency, ref_doc.posting_date)
		else:
			exchange_rate = 1
			outstanding_amount, total_amount = get_outstanding_on_journal_entry(
				reference_name, party_type, party
			)

	elif reference_doctype == "Advance Sales Invoice":
		if reverse_payment_details := frappe.db.get_all(
			"Advance Sales Invoice",
			filters={"name": reference_name},
			fields=["payment_type", "party_type"],
		)[0]:
			payment_type = reverse_payment_details.payment_type
			account_type = frappe.db.get_value(
				"Party Type", reverse_payment_details.party_type, "account_type"
			)
		exchange_rate = 1

	elif reference_doctype != "Journal Entry":
		if not total_amount:
			if party_account_currency == company_currency:
				total_amount = (
					ref_doc.get("base_rounded_total")
					or ref_doc.get("rounded_total")
					or ref_doc.get("base_grand_total")
					or ref_doc.get("grand_total")
				)
				exchange_rate = 1
			else:
				total_amount = ref_doc.get("rounded_total") or ref_doc.get("grand_total")
		if not exchange_rate:
			
			exchange_rate = ref_doc.get("conversion_rate") or get_exchange_rate(
				party_account_currency, company_currency, ref_doc.posting_date
			)

		if reference_doctype in ("Sales Invoice", "Purchase Invoice"):
			outstanding_amount = ref_doc.get("outstanding_amount")
			account = (
				ref_doc.get("debit_to") if reference_doctype == "Sales Invoice" else ref_doc.get("credit_to")
			)
		else:
			outstanding_amount = flt(total_amount) - flt(ref_doc.get("advance_paid"))

		if reference_doctype in ["Sales Order", "Purchase Order"]:
			party_type = "Customer" if reference_doctype == "Sales Order" else "Supplier"
			party_field = "customer" if reference_doctype == "Sales Order" else "supplier"
			party = ref_doc.get(party_field)
			account = get_party_account(party_type, party, ref_doc.company)
	else:
		exchange_rate = get_exchange_rate(party_account_currency, company_currency, ref_doc.posting_date)

	res = frappe._dict(
		{
			"due_date": ref_doc.get("due_date"),
			"total_amount": flt(total_amount),
			"outstanding_amount": flt(outstanding_amount),
			"exchange_rate": flt(exchange_rate),
			"bill_no": ref_doc.get("bill_no"),
			"account_type": account_type,
			"payment_type": payment_type,
		}
	)
	if account:
		res.update({"account": account})
	return res
