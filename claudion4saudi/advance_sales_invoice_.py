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
    # Note: total, grand_total, and base_total will be calculated proportionally based on paid_amount
    # Don't copy directly from Sales Order - calculate after copying items and taxes
    if hasattr(pe, "ensure_supplier_is_not_blocked"):
        pe.ensure_supplier_is_not_blocked()        

    pe.paid_from = party_account if payment_type == "Receive" else bank.account
    pe.paid_to = party_account if payment_type == "Pay" else bank.account
    pe.paid_from_account_currency = (
        party_account_currency if payment_type == "Receive" else bank.account_currency
    )
    pe.paid_to_account_currency = party_account_currency if payment_type == "Pay" else bank.account_currency
    # Auto-fill paid_amount with total WITHOUT tax (user can change it)
    pe.paid_amount = flt(doc.total)
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

    # Calculate proportion ratio for advance payment based on ITEM TOTAL (without tax)
    # User enters paid_amount WITHOUT tax (e.g., 20,000), system will add tax on top
    sales_order_total = flt(doc.total)  # Item total WITHOUT tax
    if sales_order_total > 0:
        proportion_ratio = flt(pe.paid_amount) / sales_order_total  # Use pe.paid_amount not the old paid_amount variable
    else:
        proportion_ratio = 1.0
    
    # Calculate proportional tax EARLY (needed for allocated_amount in references)
    # allocated_amount must include tax because it represents the total customer payment
    proportional_total_taxes = flt(doc.get("total_taxes_and_charges")) * proportion_ratio
    
    if dn not in existing_references:
        pe.append("references", {
            "reference_doctype": dt,
            "reference_name": dn,             
            "total_amount": financial_details.get("total_amount"),
            "outstanding_amount": financial_details.get("outstanding_amount"),
            "exchange_rate": financial_details.get("exchange_rate"),
            # allocated_amount = paid_amount + proportional_tax (total customer payment including tax)
            "allocated_amount": flt(pe.paid_amount) + proportional_total_taxes,
            "bill_no": financial_details.get("bill_no"),
            "due_date": financial_details.get("due_date"),
            "account_type": financial_details.get("account_type"),
            "payment_type": financial_details.get("payment_type"),
        })

    pe.run_method("set_missing_values") 
    pe.flags.ignore_validate = True

    # Proportion ratio already calculated above based on sales_order_total and paid_amount
    
    if not pe.get("custom_item"):
        pe.set("custom_item", [])

    # Copy items with proportional amounts based on paid_amount
    for item in doc.items:
        # Calculate proportional amounts for this advance payment
        proportional_amount = flt(item.amount) * proportion_ratio
        proportional_net_amount = flt(item.net_amount) * proportion_ratio
        proportional_base_amount = flt(item.base_amount) * proportion_ratio
        
        pe.append("custom_item", {
            "item_code": item.item_code,
            "item_name": item.item_name,	
            "delivery_date": item.delivery_date,
            "qty": item.qty,  # Keep original qty for reference
            "rate": item.rate,  # Keep original rate for reference
            "amount": proportional_amount,  # Proportional amount based on paid_amount
            "actual_qty": item.actual_qty,
            "item_tax_template": item.item_tax_template,
            "net_amount": proportional_net_amount,  # Proportional net amount
            "uom": item.uom,
            "base_amount": proportional_base_amount,  # Proportional base amount
        })

    if not pe.get("taxes"):
        pe.set("taxes", [])

    # Copy taxes with proportional amounts based on paid_amount
    for tax in doc.get("taxes"):
        # Calculate proportional tax amounts for this advance payment
        proportional_tax_amount = flt(tax.tax_amount) * proportion_ratio
        proportional_total = flt(tax.total) * proportion_ratio
        proportional_base_total = flt(tax.base_total) * proportion_ratio
        proportional_base_tax_amount = flt(tax.base_tax_amount) * proportion_ratio
        proportional_tax_after_discount = flt(tax.tax_amount_after_discount_amount) * proportion_ratio if tax.get("tax_amount_after_discount_amount") else 0
        
        # Change charge_type from "On Net Total" to "On Paid Amount" for Advance Sales Invoice
        # "On Net Total" is not valid for Advance Sales Invoice
        charge_type = "On Paid Amount" if tax.charge_type == "On Net Total" else tax.charge_type
        
        new_tax = pe.append("taxes", {
            "charge_type": charge_type,  # Use "On Paid Amount" instead of "On Net Total"
            "account_head": tax.account_head,
            "description": tax.description,
            "cost_center": tax.cost_center,
            "rate": tax.rate,  # Keep original rate for reference
            "tax_amount": proportional_tax_amount,  # Proportional tax amount
            # CRITICAL: included_in_paid_amount=0 means tax is ADDED to paid_amount
            # This matches Payment Entry behavior: user enters 20,000, system adds 3,000 tax = 23,000 total
            "included_in_paid_amount": 0,  # Tax NOT included, will be added on top
            "add_deduct_tax": "Add",  # Required field: Add or Deduct tax
            "total": proportional_total,  # Proportional total
            "base_total": proportional_base_total,  # Proportional base total
            "base_tax_amount": proportional_base_tax_amount,  # Proportional base tax amount
            "tax_amount_after_discount_amount": proportional_tax_after_discount,  # Proportional tax after discount
        })
        if hasattr(tax, "item_wise_tax_detail"):
            new_tax.item_wise_tax_detail = tax.item_wise_tax_detail
    
    # proportional_total_taxes already calculated earlier
    pe.total_taxes_and_charges = proportional_total_taxes
    
    # Calculate proportional totals for the advance payment
    proportional_total = flt(doc.get("total")) * proportion_ratio
    proportional_base_total = flt(doc.get("base_total")) * proportion_ratio
    
    # Unallocated amount should be 0 for advance invoices
    pe.unallocated_amount = 0

    if party_account and bank:
        pe.db_set("company_currency", frappe.get_cached_value("Company", pe.company, "default_currency"))

        pe.set_exchange_rate(ref_doc=doc)
        pe.set_amounts()
    
    # IMPORTANT: Set these values AFTER set_amounts() because set_amounts() overwrites received_amount
    # - paid_amount = 100,000 (items only, what user enters)
    # - tax = 15,000 (calculated and added automatically)
    # - grand_total = 115,000 (paid_amount + tax)
    pe.total = flt(pe.paid_amount)  # User-entered amount WITHOUT tax
    pe.base_total = pe.total  # Assuming same currency
    pe.grand_total = flt(pe.paid_amount) + proportional_total_taxes  # Add tax on top
    
    # CRITICAL: Update received_amount to include tax for proper GL entries
    # When tax is NOT included in paid_amount (included_in_paid_amount=0),
    # the actual amount received from customer = paid_amount + tax
    pe.received_amount = flt(pe.paid_amount) + proportional_total_taxes
    pe.base_received_amount = pe.received_amount  # Assuming same currency
    
    # Set total_allocated_amount to match received_amount (grand_total with tax)
    pe.total_allocated_amount = pe.received_amount
    
    # Difference should be 0
    pe.difference_amount = 0

    if not created_from_payment_request:
        allocate_open_payment_requests_to_references(pe.references, pe.precision("paid_amount"))

    return pe
import json
from collections import defaultdict

def generate_item_wise_tax_detail(doc):
    item_tax_map = defaultdict(lambda: [0, 0])  

    for tax in doc.get("taxes"):
        if not tax.charge_type in ["On Net Total", "On Previous Row Amount", "On Previous Row Total"]:
            continue

        if not hasattr(tax, "item_wise_tax_detail") or not tax.item_wise_tax_detail:
            continue

        try:
            tax_detail = json.loads(tax.item_wise_tax_detail)
        except Exception as e:
            frappe.logger().error(f"Could not parse item_wise_tax_detail: {e}")
            continue

        for item_code, values in tax_detail.items():
            item_tax_map[item_code][0] = values[0]  
            item_tax_map[item_code][1] += values[1]  
    return dict(item_tax_map)


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


@frappe.whitelist()
def get_company_defaults(company):
	fields = ["write_off_account", "exchange_gain_loss_account", "cost_center"]
	return frappe.get_cached_value("Company", company, fields, as_dict=1)

