# from erpnext.accounts.doctype.payment_entry.payment_entry import get_party_details
# from erpnext.setup.utils import get_exchange_rate
# from erpnext.accounts.party import get_party_account
# import frappe
# from frappe.utils import flt

# frappe.msgprint("python loads")

# @frappe.whitelist()
# def get_advance_sales_invoice_entry(sales_order):
#     sales_order_doc = frappe.get_doc("Sales Order", sales_order)

#     # Fetch Party Details
#     party_details = get_party_details(
#         company=sales_order_doc.company,
#         party_type="Customer",
#         party=sales_order_doc.customer,
#         date=sales_order_doc.transaction_date,
#     )

#     company_currency = frappe.get_cached_value("Company", sales_order_doc.company, "default_currency")

#     source_exchange_rate = 1
#     target_exchange_rate = 1

#     # Source exchange rate based on paid_from account currency
#     if party_details.get("party_account_currency") != company_currency:
#         source_exchange_rate = get_exchange_rate(
#             from_currency=party_details.get("party_account_currency"),
#             to_currency=company_currency,
#             transaction_date=sales_order_doc.transaction_date,
#         )

#     bank_account_currency = company_currency
#     if party_details.get("bank_account"):
#         bank_account_currency = frappe.get_cached_value("Account", party_details.get("bank_account"), "account_currency")
#         if bank_account_currency != company_currency:
#             target_exchange_rate = get_exchange_rate(
#                 from_currency=bank_account_currency,
#                 to_currency=company_currency,
#                 transaction_date=sales_order_doc.transaction_date,
#             )

#     # Set paid_amount to Sales Order grand total initially (but editable later)
#     paid_amount = sales_order_doc.grand_total or 0
#     base_paid_amount = paid_amount * source_exchange_rate
#     received_amount = paid_amount * (source_exchange_rate / target_exchange_rate)
#     base_received_amount = received_amount * target_exchange_rate

#     asi_data = {
#         "company": sales_order_doc.company,
#         "party_type": "Customer",
#         "party": sales_order_doc.customer,
#         "party_name": party_details.get("party_name"),
#         "party_balance": party_details.get("party_balance"),
#         "paid_from": party_details.get("party_account"),
#         "paid_to": party_details.get("bank_account"),
#         "paid_from_account_currency": party_details.get("party_account_currency"),
#         "posting_date": frappe.utils.nowdate(),
#         "reference_date": sales_order_doc.transaction_date,
#         "reference_no": sales_order_doc.name,
#         "payment_type": "Receive",
#         "paid_amount": paid_amount,
#         "base_paid_amount": base_paid_amount,
#         "received_amount": received_amount,
#         "base_received_amount": base_received_amount,
#         "source_exchange_rate": source_exchange_rate,
#         "target_exchange_rate": target_exchange_rate,
#         "payment_reference": sales_order_doc.name,
#     }

#     # # ---- Reference Details (Logic from get_reference_details) ----
#     # reference_doctype = "Sales Order"
#     # reference_name = sales_order_doc.name
#     # party_account_currency = party_details.get("party_account_currency")

#     # # Get outstanding amount and other fields as per get_reference_details logic
#     # total_amount = sales_order_doc.grand_total or 0
#     # outstanding_amount = flt(total_amount) - flt(sales_order_doc.get("advance_paid"))
#     # exchange_rate = source_exchange_rate  # Same as paid_from_account_currency exchange rate
#     # account = get_party_account("Customer", sales_order_doc.customer, sales_order_doc.company)

#     # references = [
#     #     {
#     #         "reference_doctype": reference_doctype,
#     #         "reference_name": reference_name,
#     #         "due_date": sales_order_doc.delivery_date or frappe.utils.nowdate(),
#     #         "total_amount": total_amount,
#     #         "outstanding_amount": outstanding_amount,
#     #         "allocated_amount": paid_amount,
#     #         "exchange_rate": exchange_rate,
#     #         "account": account,
#     #     }
#     # ]

#     # asi_data["references"] = references

#     # ---- Custom Items Table Mapping ----
#     custom_items = []
#     for item in sales_order_doc.items:
#         custom_items.append(
#             {
#                 "item_code": item.item_code,
#                 "delivery_date": item.delivery_date,
#                 "qty": item.qty,
#                 "rate": item.rate,
#                 "amount": item.amount,
#                 "actual_qty": item.actual_qty,
#             }
#         )
#     asi_data["custom_item"] = custom_items

#     # ---- Taxes Table Mapping ----
#     asi_taxes = []
#     for tax in sales_order_doc.taxes:
#         asi_taxes.append(
#             {
#                 "charge_type": tax.charge_type,
#                 "account_head": tax.account_head,
#                 "description": tax.description,
#                 "rate": tax.rate,
#                 "tax_amount": tax.tax_amount,
#                 "base_tax_amount": tax.base_tax_amount,
#                 "total": tax.total,
#                 "base_total": tax.base_total,
#                 "cost_center": tax.cost_center,
#             }
#         )
#     asi_data["taxes"] = asi_taxes

#     return asi_data

# from functools import reduce
# from erpnext.accounts.doctype.payment_entry.payment_entry import (
#     allocate_open_payment_requests_to_references,
#     apply_early_payment_discount,
#     get_bank_cash_account,
#     get_reference_as_per_payment_terms,
#     set_grand_total_and_outstanding_amount,
#     set_paid_amount_and_received_amount,
#     set_party_account,
#     set_party_account_currency,
#     set_party_type,
#     set_payment_type,
#     set_pending_discount_loss,
#     split_early_payment_discount_loss,
#     update_accounting_dimensions,
# )
# # from erpnext.accounts.general_ledger import update_accounting_dimensions
# from erpnext.accounts.party import get_party_bank_account
# import frappe
# from frappe import _
# from frappe.utils import flt, getdate, nowdate


# @frappe.whitelist()
# def get_payment_entry(
#     dn=None,  # Only expecting Sales Order name
#     party_amount=None,
#     bank_account=None,
#     bank_amount=None,
#     party_type=None,
#     payment_type=None,
#     reference_date=None,
#     ignore_permissions=False,
#     created_from_payment_request=False,
# ):
#     dt = "Sales Order"  # Always process a Sales Order

#     frappe.logger().info(f"Received params: dn={dn}, args={frappe.form_dict}")

#     # Fetch Sales Order from API request if not explicitly passed
#     if not dn:
#         dn = frappe.form_dict.get("sales_order")  # Try to get from request

#     if not dn:
#         frappe.throw(_("Missing required parameter: dn (Sales Order name)"), title=_("Validation Error"))

#     # Fetch the Sales Order
#     try:
#         doc = frappe.get_doc(dt, dn)
#     except frappe.DoesNotExistError:
#         frappe.throw(_("Sales Order {0} not found").format(dn), title=_("Error"))

#     if not party_type:
#         party_type = set_party_type(dt)

#     party_account = set_party_account(dt, dn, doc, party_type)
#     party_account_currency = set_party_account_currency(dt, party_account, doc)

#     if not payment_type:
#         payment_type = set_payment_type(dt, doc)

#     grand_total, outstanding_amount = set_grand_total_and_outstanding_amount(
#         party_amount, dt, party_account_currency, doc
#     )

#     # bank or cash
#     bank = get_bank_cash_account(doc, bank_account)

#     # if default bank or cash account is not set in company master and party has default company bank account, fetch it
#     if party_type in ["Customer", "Supplier"] and not bank:
#         party_bank_account = get_party_bank_account(party_type, doc.get(frappe.scrub(party_type)))
#         if party_bank_account:
#             account = frappe.db.get_value("Bank Account", party_bank_account, "account")
#             bank = get_bank_cash_account(doc, account)

#     paid_amount, received_amount = set_paid_amount_and_received_amount(
#         dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc
#     )

#     reference_date = getdate(reference_date)
#     paid_amount, received_amount, discount_amount, valid_discounts = apply_early_payment_discount(
#         paid_amount, received_amount, doc, party_account_currency, reference_date
#     )

#     pe = frappe.new_doc("Advance Sales Invoice")
#     pe.payment_type = payment_type
#     pe.company = doc.company
#     pe.cost_center = doc.get("cost_center")
#     pe.posting_date = nowdate()
#     pe.reference_date = reference_date
#     pe.mode_of_payment = doc.get("mode_of_payment")
#     pe.party_type = party_type
#     pe.party = doc.get(frappe.scrub(party_type))
#     pe.contact_person = doc.get("contact_person")
#     pe.contact_email = doc.get("contact_email")
#     if hasattr(pe, "ensure_supplier_is_not_blocked"):
#         pe.ensure_supplier_is_not_blocked()

#     pe.paid_from = party_account if payment_type == "Receive" else bank.account
#     pe.paid_to = party_account if payment_type == "Pay" else bank.account
#     pe.paid_from_account_currency = (
#         party_account_currency if payment_type == "Receive" else bank.account_currency
#     )
#     pe.paid_to_account_currency = party_account_currency if payment_type == "Pay" else bank.account_currency
#     pe.paid_amount = paid_amount
#     pe.received_amount = received_amount
#     pe.letter_head = doc.get("letter_head")
#     pe.bank_account = frappe.db.get_value("Bank Account", {"is_company_account": 1, "is_default": 1}, "name")

#     if dt in ["Purchase Order", "Sales Order", "Sales Invoice", "Purchase Invoice"]:
#         pe.project = doc.get("project") or reduce(
#             lambda prev, cur: prev or cur, [x.get("project") for x in doc.get("items")], None
#         )  # get first non-empty project from items

#     if pe.party_type in ["Customer", "Supplier"]:
#         bank_account = get_party_bank_account(pe.party_type, pe.party)
#         pe.set("party_bank_account", bank_account)
#         if hasattr(pe, "set_bank_account_data"):
#             pe.set_bank_account_data()

#     # only Purchase Invoice can be blocked individually
#     if doc.doctype == "Purchase Invoice" and doc.invoice_is_blocked():
#         frappe.msgprint(_("{0} is on hold till {1}").format(doc.name, doc.release_date))
#     else:
#         if doc.doctype in (
#             "Sales Invoice",
#             "Purchase Invoice",
#             "Purchase Order",
#             "Sales Order",
#         ) and frappe.get_cached_value(
#             "Payment Terms Template",
#             doc.payment_terms_template,
#             "allocate_payment_based_on_payment_terms",
#         ):
#             for reference in get_reference_as_per_payment_terms(
#                 doc.payment_schedule, dt, dn, doc, grand_total, outstanding_amount, party_account_currency
#             ):
#                 pe.append("references", reference)
#         else:
#             if dt == "Dunning":
#                 for overdue_payment in doc.overdue_payments:
#                     pe.append(
#                         "references",
#                         {
#                             "reference_doctype": "Sales Invoice",
#                             "reference_name": overdue_payment.sales_invoice,
#                             "payment_term": overdue_payment.payment_term,
#                             "due_date": overdue_payment.due_date,
#                             "total_amount": overdue_payment.outstanding,
#                             "outstanding_amount": overdue_payment.outstanding,
#                             "allocated_amount": overdue_payment.outstanding,
#                         },
#                     )

#                 pe.append(
#                     "deductions",
#                     {
#                         "account": doc.income_account,
#                         "cost_center": doc.cost_center,
#                         "amount": -1 * doc.dunning_amount,
#                         "description": _("Interest and/or dunning fee"),
#                     },
#                 )
#             else:
#                 pe.append(
#                     "references",
#                     {
#                         "reference_doctype": dt,
#                         "reference_name": dn,
#                         "bill_no": doc.get("bill_no"),
#                         "due_date": doc.get("due_date"),
#                         "total_amount": grand_total,
#                         "outstanding_amount": outstanding_amount,
#                         "allocated_amount": outstanding_amount,
#                     },
#                 )

    
    
#     if not pe.get("custom_item"):
#         pe.set("custom_item", [])

#     for item in doc.items:
#         pe.append("custom_item", {
#         "item_code": item.item_code,
#         "delivery_date": item.delivery_date,
#         "qty": item.qty,
#         "rate": item.rate,
#         "amount": item.amount,
#         "actual_qty": item.actual_qty,
#     })

#     # pe.setup_party_account_field()
#     # pe.set_missing_values()
#     # pe.set_missing_ref_details()
#     if hasattr(pe, "setup_party_account_field"):
#         pe.setup_party_account_field()
#     if hasattr(pe, "set_missing_values"):
#         pe.set_missing_values()
#     if hasattr(pe, "set_missing_ref_details"):
#         pe.set_missing_ref_details()

#     # if not pe.get("voucher_type"):
#     #     pe.voucher_type = "Advance Sales Invoice"

#     update_accounting_dimensions(pe, doc)
#     # update_accounting_dimensions(pe.as_dict())

#     if party_account and bank:
#         if discount_amount:
#             base_total_discount_loss = 0
#             if frappe.db.get_single_value("Accounts Settings", "book_tax_discount_loss"):
#                 base_total_discount_loss = split_early_payment_discount_loss(pe, doc, valid_discounts)

#             set_pending_discount_loss(
#                 pe, doc, discount_amount, base_total_discount_loss, party_account_currency
#             )

#         # pe.set_exchange_rate(ref_doc=doc)
#         # Ensure 'set_exchange_rate' method exists before calling it
#         if hasattr(pe, "set_exchange_rate"):
#             pe.set_exchange_rate(ref_doc=doc)
#         else:
#     # Manually set exchange rate if the method doesn't exist
#             if pe.paid_from_account_currency and pe.paid_to_account_currency:
#                 pe.conversion_rate = frappe.db.get_value(
#                 "Currency Exchange",
#                   {"from_currency": pe.paid_from_account_currency, "to_currency": pe.paid_to_account_currency},
#             "exchange_rate",
#         ) or 1.0

#         # pe.set_amounts()
#         # Ensure 'set_amounts' method exists before calling it
#     if hasattr(pe, "set_amounts"):
#         pe.set_amounts()
#     else:
#     # Manually set amounts if the method doesn't exist
#         pe.total_amount = pe.paid_amount or 0
#         pe.outstanding_amount = pe.paid_amount or 0


#     # If PE is created from PR directly, then no need to find open PRs for the references
#     if not created_from_payment_request:
#         allocate_open_payment_requests_to_references(pe.references, pe.precision("paid_amount"))

#     return pe




