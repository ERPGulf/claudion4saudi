# # # Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# # # For license information, please see license.txt

# # import json
# # from functools import reduce

# # import frappe
# # from frappe import ValidationError, _, qb, scrub, throw
# # from frappe.query_builder import Tuple
# # from frappe.query_builder.functions import Count
# # from frappe.utils import cint, comma_or, flt, getdate, nowdate
# # from frappe.utils.data import comma_and, fmt_money, get_link_to_form
# # from pypika import Case
# # from pypika.functions import Coalesce, Sum

# # import erpnext
# # from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_dimensions
# # from erpnext.accounts.general_ledger import (
# # 	make_gl_entries,
# # 	make_reverse_gl_entries,
# # 	process_gl_map,
# # )
# # from erpnext.accounts.party import get_party_account
# # from erpnext.accounts.utils import (
# # 	cancel_exchange_gain_loss_journal,
# # 	get_account_currency,
# # 	get_balance_on,
# # 	get_outstanding_invoices,
# # )
# # from erpnext.controllers.accounts_controller import (
# # 	AccountsController,
# # 	get_supplier_block_status,
# # 	validate_taxes_and_charges,
# # )
# # from erpnext.setup.utils import get_exchange_rate


# # class InvalidAdvanceSalesInvoice(ValidationError):
# # 	pass


# # class AdvanceSalesInvoice(AccountsController):
# # 	def __init__(self, *args, **kwargs):
# # 		super().__init__(*args, **kwargs)

# # 	def validate(self):
# # 		self.set_missing_values()
# # 		self.validate_payment_type()
# # 		self.validate_party_details()
# # 		self.set_exchange_rate()
# # 		self.validate_mandatory()
# # 		self.set_amounts()
# # 		self.validate_amounts()
# # 		self.set_status()
# # 		self.set_total_in_words()

# # 	def set_missing_values(self):
# # 		if self.party:
# # 			if not self.party_balance:
# # 				self.party_balance = get_balance_on(
# # 					party_type=self.party_type, party=self.party, date=self.posting_date, company=self.company
# # 				)

# # 		if self.paid_from and not (self.paid_from_account_currency or self.paid_from_account_balance):
# # 			acc = get_account_currency(self.paid_from)
# # 			self.paid_from_account_currency = acc

# # 		if self.paid_to and not (self.paid_to_account_currency or self.paid_to_account_balance):
# # 			acc = get_account_currency(self.paid_to)
# # 			self.paid_to_account_currency = acc

# # 	def validate_payment_type(self):
# # 		if self.payment_type not in ("Receive", "Pay", "Internal Transfer"):
# # 			frappe.throw(_("Payment Type must be one of Receive, Pay and Internal Transfer"))

# # 	def validate_party_details(self):
# # 		if self.party:
# # 			if not frappe.db.exists(self.party_type, self.party):
# # 				frappe.throw(_("{0} {1} does not exist").format(_(self.party_type), self.party))

# # 	def set_exchange_rate(self):
# # 		if self.paid_from_account_currency == self.company_currency:
# # 			self.source_exchange_rate = 1
# # 		else:
# # 			self.source_exchange_rate = get_exchange_rate(
# # 				self.paid_from_account_currency, self.company_currency, self.posting_date
# # 			)

# # 		if self.paid_to_account_currency == self.company_currency:
# # 			self.target_exchange_rate = 1
# # 		else:
# # 			self.target_exchange_rate = get_exchange_rate(
# # 				self.paid_to_account_currency, self.company_currency, self.posting_date
# # 			)

# # 	def validate_mandatory(self):
# # 		for field in ("paid_amount", "received_amount", "source_exchange_rate", "target_exchange_rate"):
# # 			if not self.get(field):
# # 				frappe.throw(_("{0} is mandatory").format(self.meta.get_label(field)))

# # 	def set_amounts(self):
# # 		self.base_paid_amount = flt(self.paid_amount) * flt(self.source_exchange_rate)
# # 		self.base_received_amount = flt(self.received_amount) * flt(self.target_exchange_rate)

# # 	def validate_amounts(self):
# # 		if self.paid_from_account_currency == self.paid_to_account_currency:
# # 			if self.paid_amount < self.received_amount:
# # 				frappe.throw(_("Received Amount cannot be greater than Paid Amount"))

# # 	def set_status(self):
# # 		if self.docstatus == 2:
# # 			self.status = "Cancelled"
# # 		elif self.docstatus == 1:
# # 			self.status = "Submitted"
# # 		else:
# # 			self.status = "Draft"

# # 		self.db_set("status", self.status, update_modified=True)

# # 	def set_total_in_words(self):
# # 		from frappe.utils import money_in_words

# # 		self.base_in_words = money_in_words(self.base_paid_amount, self.company_currency)
# # 		self.in_words = money_in_words(self.paid_amount, self.paid_from_account_currency)


# # 	def add_tax_gl_entries(self, gl_entries):
# # 		for d in self.get("taxes"):
# # 			account_currency = get_account_currency(d.account_head)
# # 			if account_currency != self.company_currency:
# # 				frappe.throw(_("Currency for {0} must be {1}").format(d.account_head, self.company_currency))

# # 			if self.payment_type in ("Pay", "Internal Transfer"):
# # 				dr_or_cr = "debit" if d.add_deduct_tax == "Add" else "credit"
# # 				rev_dr_or_cr = "credit" if dr_or_cr == "debit" else "debit"
# # 				against = self.party or self.paid_from
# # 			elif self.payment_type == "Receive":
# # 				dr_or_cr = "credit" if d.add_deduct_tax == "Add" else "debit"
# # 				rev_dr_or_cr = "credit" if dr_or_cr == "debit" else "debit"
# # 				against = self.party or self.paid_to

# # 			payment_account = self.get_party_account_for_taxes()
# # 			tax_amount = d.tax_amount
# # 			base_tax_amount = d.base_tax_amount

# # 			gl_entries.append(
# # 				self.get_gl_dict(
# # 					{
# # 						"account": d.account_head,
# # 						"against": against,
# # 						dr_or_cr: tax_amount,
# # 						dr_or_cr + "_in_account_currency": base_tax_amount
# # 						if account_currency == self.company_currency
# # 						else d.tax_amount,
# # 						"cost_center": d.cost_center,
# # 						"post_net_value": True,
# # 					},
# # 					account_currency,
# # 					item=d,
# # 				)
# # 			)

# # 			if not d.included_in_paid_amount:
# # 				if get_account_currency(payment_account) != self.company_currency:
# # 					if self.payment_type == "Receive":
# # 						exchange_rate = self.target_exchange_rate
# # 					elif self.payment_type in ["Pay", "Internal Transfer"]:
# # 						exchange_rate = self.source_exchange_rate
# # 					base_tax_amount = flt((tax_amount / exchange_rate), self.precision("paid_amount"))

# # 				gl_entries.append(
# # 					self.get_gl_dict(
# # 						{
# # 							"account": payment_account,
# # 							"against": against,
# # 							rev_dr_or_cr: tax_amount,
# # 							rev_dr_or_cr + "_in_account_currency": base_tax_amount
# # 							if account_currency == self.company_currency
# # 							else d.tax_amount,
# # 							"cost_center": self.cost_center,
# # 							"post_net_value": True,
# # 						},
# # 						account_currency,
# # 						item=d,
# # 					)
# # 				)

# # 	def add_deductions_gl_entries(self, gl_entries):
# # 		for d in self.get("deductions"):
# # 			if d.amount:
# # 				account_currency = get_account_currency(d.account)
# # 				if account_currency != self.company_currency:
# # 					frappe.throw(_("Currency for {0} must be {1}").format(d.account, self.company_currency))

# # 				gl_entries.append(
# # 					self.get_gl_dict(
# # 						{
# # 							"account": d.account,
# # 							"account_currency": account_currency,
# # 							"against": self.party or self.paid_from,
# # 							"debit_in_account_currency": d.amount,
# # 							"debit": d.amount,
# # 							"cost_center": d.cost_center,
# # 						},
# # 						item=d,
# # 					)
# # 				)

# # 	def get_party_account_for_taxes(self):
# # 		if self.payment_type == "Receive":
# # 			return self.paid_to
# # 		elif self.payment_type in ("Pay", "Internal Transfer"):
# # 			return self.paid_from

# # 	def get_value_in_transaction_currency(self, account_currency, gl_dict, field):
# # 		company_currency = erpnext.get_company_currency(self.company)
# # 		conversion_rate = self.target_exchange_rate
# # 		if self.paid_from_account_currency != company_currency:
# # 			conversion_rate = self.source_exchange_rate

# # 		return flt(gl_dict.get(field, 0) / (conversion_rate or 1))

# # 	def update_advance_paid(self):
# # 		if self.payment_type in ("Receive", "Pay") and self.party:
# # 			for d in self.get("references"):
# # 				if d.allocated_amount and d.reference_doctype in frappe.get_hooks("advance_payment_doctypes"):
# # 					frappe.get_doc(
# # 						d.reference_doctype, d.reference_name, for_update=True
# # 					).set_total_advance_paid()

# # 	def on_recurring(self, reference_doc, auto_repeat_doc):
# # 		self.reference_no = reference_doc.name
# # 		self.reference_date = nowdate()

# # 	def calculate_deductions(self, tax_details):
# # 		return {
# # 			"account": tax_details["tax"]["account_head"],
# # 			"cost_center": frappe.get_cached_value("Company", self.company, "cost_center"),
# # 			"amount": self.total_allocated_amount * (tax_details["tax"]["rate"] / 100),
# # 		}

# # 	def set_gain_or_loss(self, account_details=None):
# # 		if not self.difference_amount:
# # 			self.set_difference_amount()

# # 		row = {"amount": self.difference_amount}

# # 		if account_details:
# # 			row.update(account_details)

# # 		if not row.get("amount"):
# # 			# if no difference amount
# # 			return

# # 		self.append("deductions", row)
# # 		self.set_unallocated_amount()

# # 	def get_exchange_rate(self):
# # 		return self.source_exchange_rate if self.payment_type == "Receive" else self.target_exchange_rate

# # 	def initialize_taxes(self):
# # 		for tax in self.get("taxes"):
# # 			validate_taxes_and_charges(tax)
# # 			validate_inclusive_tax(tax, self)

# # 			tax_fields = ["total", "tax_fraction_for_current_item", "grand_total_fraction_for_current_item"]

# # 			if tax.charge_type != "Actual":
# # 				tax_fields.append("tax_amount")

# # 			for fieldname in tax_fields:
# # 				tax.set(fieldname, 0.0)

# # 		self.paid_amount_after_tax = self.base_paid_amount

# # 	def determine_exclusive_rate(self):
# # 		if not any(cint(tax.included_in_paid_amount) for tax in self.get("taxes")):
# # 			return

# # 		cumulated_tax_fraction = 0
# # 		for i, tax in enumerate(self.get("taxes")):
# # 			tax.tax_fraction_for_current_item = self.get_current_tax_fraction(tax)
# # 			if i == 0:
# # 				tax.grand_total_fraction_for_current_item = 1 + tax.tax_fraction_for_current_item
# # 			else:
# # 				tax.grand_total_fraction_for_current_item = (
# # 					self.get("taxes")[i - 1].grand_total_fraction_for_current_item
# # 					+ tax.tax_fraction_for_current_item
# # 				)

# # 			cumulated_tax_fraction += tax.tax_fraction_for_current_item

# # 		self.paid_amount_after_tax = flt(self.base_paid_amount / (1 + cumulated_tax_fraction))

# # 	def calculate_taxes(self):
# # 		self.total_taxes_and_charges = 0.0
# # 		self.base_total_taxes_and_charges = 0.0

# # 		actual_tax_dict = dict(
# # 			[
# # 				[tax.idx, flt(tax.tax_amount, tax.precision("tax_amount"))]
# # 				for tax in self.get("taxes")
# # 				if tax.charge_type == "Actual"
# # 			]
# # 		)

# # 		for i, tax in enumerate(self.get("taxes")):
# # 			current_tax_amount = self.get_current_tax_amount(tax)

# # 			if tax.charge_type == "Actual":
# # 				actual_tax_dict[tax.idx] -= current_tax_amount
# # 				if i == len(self.get("taxes")) - 1:
# # 					current_tax_amount += actual_tax_dict[tax.idx]

# # 			tax.tax_amount = current_tax_amount
# # 			tax.base_tax_amount = current_tax_amount

# # 			if tax.add_deduct_tax == "Deduct":
# # 				current_tax_amount *= -1.0
# # 			else:
# # 				current_tax_amount *= 1.0

# # 			if i == 0:
# # 				tax.total = flt(self.paid_amount_after_tax + current_tax_amount, self.precision("total", tax))
# # 			else:
# # 				tax.total = flt(
# # 					self.get("taxes")[i - 1].total + current_tax_amount, self.precision("total", tax)
# # 				)

# # 			tax.base_total = tax.total

# # 			if self.payment_type == "Pay":
# # 				if tax.currency != self.paid_to_account_currency:
# # 					self.total_taxes_and_charges += flt(current_tax_amount / self.target_exchange_rate)
# # 				else:
# # 					self.total_taxes_and_charges += current_tax_amount
# # 			elif self.payment_type == "Receive":
# # 				if tax.currency != self.paid_from_account_currency:
# # 					self.total_taxes_and_charges += flt(current_tax_amount / self.source_exchange_rate)
# # 				else:
# # 					self.total_taxes_and_charges += current_tax_amount

# # 			self.base_total_taxes_and_charges += tax.base_tax_amount

# # 		if self.get("taxes"):
# # 			self.paid_amount_after_tax = self.get("taxes")[-1].base_total

# # 	def get_current_tax_amount(self, tax):
# # 		tax_rate = tax.rate

# # 		# To set row_id by default as previous row.
# # 		if tax.charge_type in ["On Previous Row Amount", "On Previous Row Total"]:
# # 			if tax.idx == 1:
# # 				frappe.throw(
# # 					_(
# # 						"Cannot select charge type as 'On Previous Row Amount' or 'On Previous Row Total' for first row"
# # 					)
# # 				)

# # 			if not tax.row_id:
# # 				tax.row_id = tax.idx - 1

# # 		if tax.charge_type == "Actual":
# # 			current_tax_amount = flt(tax.tax_amount, self.precision("tax_amount", tax))
# # 		elif tax.charge_type == "On Paid Amount":
# # 			current_tax_amount = (tax_rate / 100.0) * self.paid_amount_after_tax
# # 		elif tax.charge_type == "On Previous Row Amount":
# # 			current_tax_amount = (tax_rate / 100.0) * self.get("taxes")[cint(tax.row_id) - 1].tax_amount

# # 		elif tax.charge_type == "On Previous Row Total":
# # 			current_tax_amount = (tax_rate / 100.0) * self.get("taxes")[cint(tax.row_id) - 1].total

# # 		return current_tax_amount

# # 	def get_current_tax_fraction(self, tax):
# # 		current_tax_fraction = 0

# # 		if cint(tax.included_in_paid_amount):
# # 			tax_rate = tax.rate

# # 			if tax.charge_type == "On Paid Amount":
# # 				current_tax_fraction = tax_rate / 100.0
# # 			elif tax.charge_type == "On Previous Row Amount":
# # 				current_tax_fraction = (tax_rate / 100.0) * self.get("taxes")[
# # 					cint(tax.row_id) - 1
# # 				].tax_fraction_for_current_item
# # 			elif tax.charge_type == "On Previous Row Total":
# # 				current_tax_fraction = (tax_rate / 100.0) * self.get("taxes")[
# # 					cint(tax.row_id) - 1
# # 				].grand_total_fraction_for_current_item

# # 		if getattr(tax, "add_deduct_tax", None) and tax.add_deduct_tax == "Deduct":
# # 			current_tax_fraction *= -1.0

# # 		return current_tax_fraction

# # 	def set_matched_unset_payment_requests_to_response(self):
# # 		"""
# # 		Find matched Payment Requests for those references which have no Payment Request set.\n
# # 		And set to `frappe.response` to show in the frontend for allocation.
# # 		"""
# # 		if not self.references:
# # 			return

# # 		matched_payment_requests = get_matched_payment_request_of_references(
# # 			[row for row in self.references if not row.payment_request]
# # 		)

# # 		if not matched_payment_requests:
# # 			return

# # 		frappe.response["matched_payment_requests"] = matched_payment_requests

# # 	@frappe.whitelist()
# # 	def allocate_amount_to_references(self, paid_amount, paid_amount_change, allocate_payment_amount):
# # 		"""
# # 		Allocate `Allocated Amount` and `Payment Request` against `Reference` based on `Paid Amount` and `Outstanding Amount`.\n
# # 		:param paid_amount: Paid Amount / Received Amount.
# # 		:param paid_amount_change: Flag to check if `Paid Amount` is changed or not.
# # 		:param allocate_payment_amount: Flag to allocate amount or not. (Payment Request is also dependent on this flag)
# # 		"""
# # 		if not self.references:
# # 			return

# # 		if not allocate_payment_amount:
# # 			for ref in self.references:
# # 				ref.allocated_amount = 0
# # 			return

# # 		# calculating outstanding amounts
# # 		precision = self.precision("paid_amount")
# # 		total_positive_outstanding_including_order = 0
# # 		total_negative_outstanding = 0
# # 		paid_amount -= sum(flt(d.amount, precision) for d in self.deductions)

# # 		for ref in self.references:
# # 			reference_outstanding_amount = flt(ref.outstanding_amount)
# # 			abs_outstanding_amount = abs(reference_outstanding_amount)

# # 			if reference_outstanding_amount > 0:
# # 				total_positive_outstanding_including_order += abs_outstanding_amount
# # 			else:
# # 				total_negative_outstanding += abs_outstanding_amount

# # 		# calculating allocated outstanding amounts
# # 		allocated_negative_outstanding = 0
# # 		allocated_positive_outstanding = 0

# # 		# checking party type and payment type
# # 		if (self.payment_type == "Receive" and self.party_type == "Customer") or (
# # 			self.payment_type == "Pay" and self.party_type in ("Supplier", "Employee")
# # 		):
# # 			if total_positive_outstanding_including_order > paid_amount:
# # 				remaining_outstanding = flt(
# # 					total_positive_outstanding_including_order - paid_amount, precision
# # 				)
# # 				allocated_negative_outstanding = min(remaining_outstanding, total_negative_outstanding)

# # 			allocated_positive_outstanding = paid_amount + allocated_negative_outstanding

# # 		elif self.party_type in ("Supplier", "Employee"):
# # 			if paid_amount > total_negative_outstanding:
# # 				if total_negative_outstanding == 0:
# # 					frappe.msgprint(
# # 						_("Cannot {0} from {1} without any negative outstanding invoice").format(
# # 							self.payment_type,
# # 							self.party_type,
# # 						)
# # 					)
# # 				else:
# # 					frappe.msgprint(
# # 						_("Paid Amount cannot be greater than total negative outstanding amount {0}").format(
# # 							total_negative_outstanding
# # 						)
# # 					)

# # 				return

# # 			else:
# # 				allocated_positive_outstanding = flt(total_negative_outstanding - paid_amount, precision)
# # 				allocated_negative_outstanding = paid_amount + min(
# # 					total_positive_outstanding_including_order, allocated_positive_outstanding
# # 				)

# # 		# inner function to set `allocated_amount` to those row which have no PR
# # 		def _allocation_to_unset_pr_row(
# # 			row, outstanding_amount, allocated_positive_outstanding, allocated_negative_outstanding
# # 		):
# # 			if outstanding_amount > 0 and allocated_positive_outstanding >= 0:
# # 				row.allocated_amount = min(allocated_positive_outstanding, outstanding_amount)
# # 				allocated_positive_outstanding = flt(
# # 					allocated_positive_outstanding - row.allocated_amount, precision
# # 				)
# # 			elif outstanding_amount < 0 and allocated_negative_outstanding:
# # 				row.allocated_amount = min(allocated_negative_outstanding, abs(outstanding_amount)) * -1
# # 				allocated_negative_outstanding = flt(
# # 					allocated_negative_outstanding - abs(row.allocated_amount), precision
# # 				)
# # 			return allocated_positive_outstanding, allocated_negative_outstanding

# # 		# allocate amount based on `paid_amount` is changed or not
# # 		if not paid_amount_change:
# # 			for ref in self.references:
# # 				allocated_positive_outstanding, allocated_negative_outstanding = _allocation_to_unset_pr_row(
# # 					ref,
# # 					ref.outstanding_amount,
# # 					allocated_positive_outstanding,
# # 					allocated_negative_outstanding,
# # 				)

# # 			allocate_open_payment_requests_to_references(self.references, self.precision("paid_amount"))

# # 		else:
# # 			payment_request_outstanding_amounts = (
# # 				get_payment_request_outstanding_set_in_references(self.references) or {}
# # 			)
# # 			references_outstanding_amounts = get_references_outstanding_amount(self.references) or {}
# # 			remaining_references_allocated_amounts = references_outstanding_amounts.copy()

# # 			# Re allocate amount to those references which have PR set (Higher priority)
# # 			for ref in self.references:
# # 				if not ref.payment_request:
# # 					continue

# # 				# fetch outstanding_amount of `Reference` (Payment Term) and `Payment Request` to allocate new amount
# # 				key = (ref.reference_doctype, ref.reference_name, ref.get("payment_term"))
# # 				reference_outstanding_amount = references_outstanding_amounts[key]
# # 				pr_outstanding_amount = payment_request_outstanding_amounts[ref.payment_request]

# # 				if reference_outstanding_amount > 0 and allocated_positive_outstanding >= 0:
# # 					# allocate amount according to outstanding amounts
# # 					outstanding_amounts = (
# # 						allocated_positive_outstanding,
# # 						reference_outstanding_amount,
# # 						pr_outstanding_amount,
# # 					)

# # 					ref.allocated_amount = min(outstanding_amounts)

# # 					# update amounts to track allocation
# # 					allocated_amount = ref.allocated_amount
# # 					allocated_positive_outstanding = flt(
# # 						allocated_positive_outstanding - allocated_amount, precision
# # 					)
# # 					remaining_references_allocated_amounts[key] = flt(
# # 						remaining_references_allocated_amounts[key] - allocated_amount, precision
# # 					)
# # 					payment_request_outstanding_amounts[ref.payment_request] = flt(
# # 						payment_request_outstanding_amounts[ref.payment_request] - allocated_amount, precision
# # 					)

# # 				elif reference_outstanding_amount < 0 and allocated_negative_outstanding:
# # 					# allocate amount according to outstanding amounts
# # 					outstanding_amounts = (
# # 						allocated_negative_outstanding,
# # 						abs(reference_outstanding_amount),
# # 						pr_outstanding_amount,
# # 					)

# # 					ref.allocated_amount = min(outstanding_amounts) * -1

# # 					# update amounts to track allocation
# # 					allocated_amount = abs(ref.allocated_amount)
# # 					allocated_negative_outstanding = flt(
# # 						allocated_negative_outstanding - allocated_amount, precision
# # 					)
# # 					remaining_references_allocated_amounts[key] += allocated_amount  # negative amount
# # 					payment_request_outstanding_amounts[ref.payment_request] = flt(
# # 						payment_request_outstanding_amounts[ref.payment_request] - allocated_amount, precision
# # 					)
# # 			# Re allocate amount to those references which have no PR (Lower priority)
# # 			for ref in self.references:
# # 				if ref.payment_request:
# # 					continue

# # 				key = (ref.reference_doctype, ref.reference_name, ref.get("payment_term"))
# # 				reference_outstanding_amount = remaining_references_allocated_amounts[key]

# # 				allocated_positive_outstanding, allocated_negative_outstanding = _allocation_to_unset_pr_row(
# # 					ref,
# # 					reference_outstanding_amount,
# # 					allocated_positive_outstanding,
# # 					allocated_negative_outstanding,
# # 				)

# # 	@frappe.whitelist()
# # 	def set_matched_payment_requests(self, matched_payment_requests):
# # 		"""
# # 		Set `Payment Request` against `Reference` based on `matched_payment_requests`.\n
# # 		:param matched_payment_requests: List of tuple of matched Payment Requests.

# # 		---
# # 		Example: [(reference_doctype, reference_name, allocated_amount, payment_request), ...]
# # 		"""
# # 		if not self.references or not matched_payment_requests:
# # 			return

# # 		if isinstance(matched_payment_requests, str):
# # 			matched_payment_requests = json.loads(matched_payment_requests)

# # 		# modify matched_payment_requests
# # 		# like (reference_doctype, reference_name, allocated_amount): payment_request
# # 		payment_requests = {}

# # 		for row in matched_payment_requests:
# # 			key = tuple(row[:3])
# # 			payment_requests[key] = row[3]

# # 		for ref in self.references:
# # 			if ref.payment_request:
# # 				continue

# # 			key = (ref.reference_doctype, ref.reference_name, ref.allocated_amount)

# # 			if key in payment_requests:
# # 				ref.payment_request = payment_requests[key]
# # 				del payment_requests[key]  # to avoid duplicate allocation


# # def get_matched_payment_request_of_references(references=None):
# # 	"""
# # 	Get those `Payment Requests` which are matched with `References`.\n
# # 	        - Amount must be same.
# # 	        - Only single `Payment Request` available for this amount.

# # 	Example: [(reference_doctype, reference_name, allocated_amount, payment_request), ...]
# # 	"""
# # 	if not references:
# # 		return

# # 	# to fetch matched rows
# # 	refs = {
# # 		(row.reference_doctype, row.reference_name, row.allocated_amount)
# # 		for row in references
# # 		if row.reference_doctype and row.reference_name and row.allocated_amount
# # 	}

# # 	if not refs:
# # 		return

# # 	PR = frappe.qb.DocType("Payment Request")

# # 	# query to group by reference_doctype, reference_name, outstanding_amount
# # 	subquery = (
# # 		frappe.qb.from_(PR)
# # 		.select(
# # 			PR.reference_doctype,
# # 			PR.reference_name,
# # 			PR.outstanding_amount.as_("allocated_amount"),
# # 			PR.name.as_("payment_request"),
# # 			Count("*").as_("count"),
# # 		)
# # 		.where(Tuple(PR.reference_doctype, PR.reference_name, PR.outstanding_amount).isin(refs))
# # 		.where(PR.status != "Paid")
# # 		.where(PR.docstatus == 1)
# # 		.groupby(PR.reference_doctype, PR.reference_name, PR.outstanding_amount)
# # 	)

# # 	# query to fetch matched rows which are single
# # 	matched_prs = (
# # 		frappe.qb.from_(subquery)
# # 		.select(
# # 			subquery.reference_doctype,
# # 			subquery.reference_name,
# # 			subquery.allocated_amount,
# # 			subquery.payment_request,
# # 		)
# # 		.where(subquery.count == 1)
# # 		.run()
# # 	)

# # 	return matched_prs if matched_prs else None


# # def get_references_outstanding_amount(references=None):
# # 	"""
# # 	Fetch accurate outstanding amount of `References`.\n
# # 	    - If `Payment Term` is set, then fetch outstanding amount from `Payment Schedule`.
# # 	    - If `Payment Term` is not set, then fetch outstanding amount from `References` it self.

# # 	Example: {(reference_doctype, reference_name, payment_term): outstanding_amount, ...}
# # 	"""
# # 	if not references:
# # 		return

# # 	refs_with_payment_term = get_outstanding_of_references_with_payment_term(references) or {}
# # 	refs_without_payment_term = get_outstanding_of_references_with_no_payment_term(references) or {}

# # 	return {**refs_with_payment_term, **refs_without_payment_term}


# # def get_outstanding_of_references_with_payment_term(references=None):
# # 	"""
# # 	Fetch outstanding amount of `References` which have `Payment Term` set.\n
# # 	Example: {(reference_doctype, reference_name, payment_term): outstanding_amount, ...}
# # 	"""
# # 	if not references:
# # 		return

# # 	refs = {
# # 		(row.reference_doctype, row.reference_name, row.payment_term)
# # 		for row in references
# # 		if row.reference_doctype and row.reference_name and row.payment_term
# # 	}

# # 	if not refs:
# # 		return

# # 	PS = frappe.qb.DocType("Payment Schedule")

# # 	response = (
# # 		frappe.qb.from_(PS)
# # 		.select(PS.parenttype, PS.parent, PS.payment_term, PS.outstanding)
# # 		.where(Tuple(PS.parenttype, PS.parent, PS.payment_term).isin(refs))
# # 	).run(as_dict=True)

# # 	if not response:
# # 		return

# # 	return {(row.parenttype, row.parent, row.payment_term): row.outstanding for row in response}


# # def get_outstanding_of_references_with_no_payment_term(references):
# # 	"""
# # 	Fetch outstanding amount of `References` which have no `Payment Term` set.\n
# # 	        - Fetch outstanding amount from `References` it self.

# # 	Note: `None` is used for allocation of `Payment Request`
# # 	Example: {(reference_doctype, reference_name, None): outstanding_amount, ...}
# # 	"""
# # 	if not references:
# # 		return

# # 	outstanding_amounts = {}

# # 	for ref in references:
# # 		if ref.payment_term:
# # 			continue

# # 		key = (ref.reference_doctype, ref.reference_name, None)

# # 		if key not in outstanding_amounts:
# # 			outstanding_amounts[key] = ref.outstanding_amount

# # 	return outstanding_amounts


# # def get_payment_request_outstanding_set_in_references(references=None):
# # 	"""
# # 	Fetch outstanding amount of `Payment Request` which are set in `References`.\n
# # 	Example: {payment_request: outstanding_amount, ...}
# # 	"""
# # 	if not references:
# # 		return

# # 	referenced_payment_requests = {row.payment_request for row in references if row.payment_request}

# # 	if not referenced_payment_requests:
# # 		return

# # 	PR = frappe.qb.DocType("Payment Request")

# # 	response = (
# # 		frappe.qb.from_(PR)
# # 		.select(PR.name, PR.outstanding_amount)
# # 		.where(PR.name.isin(referenced_payment_requests))
# # 	).run()

# # 	return dict(response) if response else None


# # def validate_inclusive_tax(tax, doc):
# # 	def _on_previous_row_error(row_range):
# # 		throw(
# # 			_("To include tax in row {0} in Item rate, taxes in rows {1} must also be included").format(
# # 				tax.idx, row_range
# # 			)
# # 		)

# # 	if cint(getattr(tax, "included_in_paid_amount", None)):
# # 		if tax.charge_type == "Actual":
# # 			# inclusive tax cannot be of type Actual
# # 			throw(
# # 				_("Charge of type 'Actual' in row {0} cannot be included in Item Rate or Paid Amount").format(
# # 					tax.idx
# # 				)
# # 			)
# # 		elif tax.charge_type == "On Previous Row Amount" and not cint(
# # 			doc.get("taxes")[cint(tax.row_id) - 1].included_in_paid_amount
# # 		):
# # 			# referred row should also be inclusive
# # 			_on_previous_row_error(tax.row_id)
# # 		elif tax.charge_type == "On Previous Row Total" and not all(
# # 			[cint(t.included_in_paid_amount for t in doc.get("taxes")[: cint(tax.row_id) - 1])]
# # 		):
# # 			# all rows about the referred tax should be inclusive
# # 			_on_previous_row_error("1 - %d" % (cint(tax.row_id),))
# # 		elif tax.get("category") == "Valuation":
# # 			frappe.throw(_("Valuation type charges can not be marked as Inclusive"))


# # @frappe.whitelist()
# # def get_outstanding_reference_documents(args, validate=False):
# # 	if isinstance(args, str):
# # 		args = json.loads(args)

# # 	if args.get("party_type") == "Member":
# # 		return

# # 	if not args.get("get_outstanding_invoices") and not args.get("get_orders_to_be_billed"):
# # 		args["get_outstanding_invoices"] = True

# # 	ple = qb.DocType("Payment Ledger Entry")
# # 	common_filter = []
# # 	accounting_dimensions_filter = []
# # 	posting_and_due_date = []

# # 	# confirm that Supplier is not blocked
# # 	if args.get("party_type") == "Supplier":
# # 		supplier_status = get_supplier_block_status(args["party"])
# # 		if supplier_status["on_hold"]:
# # 			if supplier_status["hold_type"] == "All":
# # 				return []
# # 			elif supplier_status["hold_type"] == "Payments":
# # 				if (
# # 					not supplier_status["release_date"]
# # 					or getdate(nowdate()) <= supplier_status["release_date"]
# # 				):
# # 					return []

# # 	party_account_currency = get_account_currency(args.get("party_account"))
# # 	company_currency = frappe.get_cached_value("Company", args.get("company"), "default_currency")

# # 	# Get positive outstanding sales /purchase invoices
# # 	condition = ""
# # 	if args.get("voucher_type") and args.get("voucher_no"):
# # 		condition = " and voucher_type={} and voucher_no={}".format(
# # 			frappe.db.escape(args["voucher_type"]), frappe.db.escape(args["voucher_no"])
# # 		)
# # 		common_filter.append(ple.voucher_type == args["voucher_type"])
# # 		common_filter.append(ple.voucher_no == args["voucher_no"])

# # 	# Add cost center condition
# # 	if args.get("cost_center"):
# # 		condition += " and cost_center='%s'" % args.get("cost_center")
# # 		accounting_dimensions_filter.append(ple.cost_center == args.get("cost_center"))

# # 	# dynamic dimension filters
# # 	active_dimensions = get_dimensions()[0]
# # 	for dim in active_dimensions:
# # 		if args.get(dim.fieldname):
# # 			condition += f" and {dim.fieldname}='{args.get(dim.fieldname)}'"
# # 			accounting_dimensions_filter.append(ple[dim.fieldname] == args.get(dim.fieldname))

# # 	date_fields_dict = {
# # 		"posting_date": ["from_posting_date", "to_posting_date"],
# # 		"due_date": ["from_due_date", "to_due_date"],
# # 	}

# # 	for fieldname, date_fields in date_fields_dict.items():
# # 		if args.get(date_fields[0]) and args.get(date_fields[1]):
# # 			condition += " and {} between '{}' and '{}'".format(
# # 				fieldname, args.get(date_fields[0]), args.get(date_fields[1])
# # 			)
# # 			posting_and_due_date.append(ple[fieldname][args.get(date_fields[0]) : args.get(date_fields[1])])
# # 		elif args.get(date_fields[0]):
# # 			# if only from date is supplied
# # 			condition += f" and {fieldname} >= '{args.get(date_fields[0])}'"
# # 			posting_and_due_date.append(ple[fieldname].gte(args.get(date_fields[0])))
# # 		elif args.get(date_fields[1]):
# # 			# if only to date is supplied
# # 			condition += f" and {fieldname} <= '{args.get(date_fields[1])}'"
# # 			posting_and_due_date.append(ple[fieldname].lte(args.get(date_fields[1])))

# # 	if args.get("company"):
# # 		condition += " and company = {}".format(frappe.db.escape(args.get("company")))
# # 		common_filter.append(ple.company == args.get("company"))

# # 	outstanding_invoices = []
# # 	negative_outstanding_invoices = []

# # 	party_account = args.get("party_account")

# # 	# get party account if advance account is set.
# # 	if args.get("book_advance_payments_in_separate_party_account"):
# # 		accounts = get_party_account(
# # 			args.get("party_type"), args.get("party"), args.get("company"), include_advance=True
# # 		)
# # 		advance_account = accounts[1] if len(accounts) >= 1 else None

# # 		if party_account == advance_account:
# # 			party_account = accounts[0]

# # 	if args.get("get_outstanding_invoices"):
# # 		outstanding_invoices = get_outstanding_invoices(
# # 			args.get("party_type"),
# # 			args.get("party"),
# # 			[party_account],
# # 			common_filter=common_filter,
# # 			posting_date=posting_and_due_date,
# # 			min_outstanding=args.get("outstanding_amt_greater_than"),
# # 			max_outstanding=args.get("outstanding_amt_less_than"),
# # 			accounting_dimensions=accounting_dimensions_filter,
# # 			vouchers=args.get("vouchers") or None,
# # 		)

# # 		outstanding_invoices = split_invoices_based_on_payment_terms(
# # 			outstanding_invoices, args.get("company")
# # 		)

# # 		for d in outstanding_invoices:
# # 			d["exchange_rate"] = 1
# # 			if party_account_currency != company_currency:
# # 				if d.voucher_type in frappe.get_hooks("invoice_doctypes"):
# # 					d["exchange_rate"] = frappe.db.get_value(d.voucher_type, d.voucher_no, "conversion_rate")
# # 				elif d.voucher_type == "Journal Entry":
# # 					d["exchange_rate"] = get_exchange_rate(
# # 						party_account_currency, company_currency, d.posting_date
# # 					)
# # 			if d.voucher_type in ("Purchase Invoice"):
# # 				d["bill_no"] = frappe.db.get_value(d.voucher_type, d.voucher_no, "bill_no")

# # 		# Get negative outstanding sales /purchase invoices
# # 		if args.get("party_type") != "Employee":
# # 			negative_outstanding_invoices = get_negative_outstanding_invoices(
# # 				args.get("party_type"),
# # 				args.get("party"),
# # 				args.get("party_account"),
# # 				party_account_currency,
# # 				company_currency,
# # 				condition=condition,
# # 			)

# # 	# Get all SO / PO which are not fully billed or against which full advance not paid
# # 	orders_to_be_billed = []
# # 	if args.get("get_orders_to_be_billed"):
# # 		orders_to_be_billed = get_orders_to_be_billed(
# # 			args.get("posting_date"),
# # 			args.get("party_type"),
# # 			args.get("party"),
# # 			args.get("company"),
# # 			party_account_currency,
# # 			company_currency,
# # 			filters=args,
# # 		)

# # 	data = negative_outstanding_invoices + outstanding_invoices + orders_to_be_billed

# # 	if not data:
# # 		if args.get("get_outstanding_invoices") and args.get("get_orders_to_be_billed"):
# # 			ref_document_type = "invoices or orders"
# # 		elif args.get("get_outstanding_invoices"):
# # 			ref_document_type = "invoices"
# # 		elif args.get("get_orders_to_be_billed"):
# # 			ref_document_type = "orders"

# # 		if not validate:
# # 			frappe.msgprint(
# # 				_(
# # 					"No outstanding {0} found for the {1} {2} which qualify the filters you have specified."
# # 				).format(
# # 					_(ref_document_type), _(args.get("party_type")).lower(), frappe.bold(args.get("party"))
# # 				)
# # 			)

# # 	return data


# # def split_invoices_based_on_payment_terms(outstanding_invoices, company) -> list:
# # 	"""Split a list of invoices based on their payment terms."""
# # 	exc_rates = get_currency_data(outstanding_invoices, company)

# # 	outstanding_invoices_after_split = []
# # 	for entry in outstanding_invoices:
# # 		if entry.voucher_type in ["Sales Invoice", "Purchase Invoice"]:
# # 			if payment_term_template := frappe.db.get_value(
# # 				entry.voucher_type, entry.voucher_no, "payment_terms_template"
# # 			):
# # 				split_rows = get_split_invoice_rows(entry, payment_term_template, exc_rates)
# # 				if not split_rows:
# # 					continue

# # 				if len(split_rows) > 1:
# # 					frappe.msgprint(
# # 						_("Splitting {0} {1} into {2} rows as per Payment Terms").format(
# # 							_(entry.voucher_type), frappe.bold(entry.voucher_no), len(split_rows)
# # 						),
# # 						alert=True,
# # 					)
# # 				outstanding_invoices_after_split += split_rows
# # 				continue

# # 		# If not an invoice or no payment terms template, add as it is
# # 		outstanding_invoices_after_split.append(entry)

# # 	return outstanding_invoices_after_split


# # def get_currency_data(outstanding_invoices: list, company: str | None = None) -> dict:
# # 	"""Get currency and conversion data for a list of invoices."""
# # 	exc_rates = frappe._dict()
# # 	company_currency = frappe.db.get_value("Company", company, "default_currency") if company else None

# # 	for doctype in ["Sales Invoice", "Purchase Invoice"]:
# # 		invoices = [x.voucher_no for x in outstanding_invoices if x.voucher_type == doctype]
# # 		for x in frappe.db.get_all(
# # 			doctype,
# # 			filters={"name": ["in", invoices]},
# # 			fields=["name", "currency", "conversion_rate", "party_account_currency"],
# # 		):
# # 			exc_rates[x.name] = frappe._dict(
# # 				conversion_rate=x.conversion_rate,
# # 				currency=x.currency,
# # 				party_account_currency=x.party_account_currency,
# # 				company_currency=company_currency,
# # 			)

# # 	return exc_rates


# # def get_split_invoice_rows(invoice: dict, payment_term_template: str, exc_rates: dict) -> list:
# # 	"""Split invoice based on its payment schedule table."""
# # 	split_rows = []
# # 	allocate_payment_based_on_payment_terms = frappe.db.get_value(
# # 		"Payment Terms Template", payment_term_template, "allocate_payment_based_on_payment_terms"
# # 	)

# # 	if not allocate_payment_based_on_payment_terms:
# # 		return [invoice]

# # 	payment_schedule = frappe.get_all(
# # 		"Payment Schedule", filters={"parent": invoice.voucher_no}, fields=["*"], order_by="due_date"
# # 	)
# # 	for payment_term in payment_schedule:
# # 		if not payment_term.outstanding > 0.1:
# # 			continue

# # 		doc_details = exc_rates.get(payment_term.parent, None)
# # 		is_multi_currency_acc = (doc_details.currency != doc_details.company_currency) and (
# # 			doc_details.party_account_currency != doc_details.company_currency
# # 		)
# # 		payment_term_outstanding = flt(payment_term.outstanding)
# # 		if not is_multi_currency_acc:
# # 			payment_term_outstanding = doc_details.conversion_rate * flt(payment_term.outstanding)

# # 		split_rows.append(
# # 			frappe._dict(
# # 				{
# # 					"due_date": invoice.due_date,
# # 					"currency": invoice.currency,
# # 					"voucher_no": invoice.voucher_no,
# # 					"voucher_type": invoice.voucher_type,
# # 					"posting_date": invoice.posting_date,
# # 					"invoice_amount": flt(invoice.invoice_amount),
# # 					"outstanding_amount": payment_term_outstanding
# # 					if payment_term_outstanding
# # 					else invoice.outstanding_amount,
# # 					"payment_term_outstanding": payment_term_outstanding,
# # 					"payment_amount": payment_term.payment_amount,
# # 					"payment_term": payment_term.payment_term,
# # 				}
# # 			)
# # 		)

# # 	return split_rows


# # def get_orders_to_be_billed(
# # 	posting_date,
# # 	party_type,
# # 	party,
# # 	company,
# # 	party_account_currency,
# # 	company_currency,
# # 	cost_center=None,
# # 	filters=None,
# # ):
# # 	voucher_type = None
# # 	if party_type == "Customer":
# # 		voucher_type = "Sales Order"
# # 	elif party_type == "Supplier":
# # 		voucher_type = "Purchase Order"

# # 	if not voucher_type:
# # 		return []

# # 	# Add cost center condition
# # 	doc = frappe.get_doc({"doctype": voucher_type})
# # 	condition = ""
# # 	if doc and hasattr(doc, "cost_center") and doc.cost_center:
# # 		condition = " and cost_center='%s'" % cost_center

# # 	# dynamic dimension filters
# # 	active_dimensions = get_dimensions()[0]
# # 	for dim in active_dimensions:
# # 		if filters.get(dim.fieldname):
# # 			condition += f" and {dim.fieldname}='{filters.get(dim.fieldname)}'"

# # 	if party_account_currency == company_currency:
# # 		grand_total_field = "base_grand_total"
# # 		rounded_total_field = "base_rounded_total"
# # 	else:
# # 		grand_total_field = "grand_total"
# # 		rounded_total_field = "rounded_total"

# # 	orders = frappe.db.sql(
# # 		"""
# # 		select
# # 			name as voucher_no,
# # 			if({rounded_total_field}, {rounded_total_field}, {grand_total_field}) as invoice_amount,
# # 			(if({rounded_total_field}, {rounded_total_field}, {grand_total_field}) - advance_paid) as outstanding_amount,
# # 			transaction_date as posting_date
# # 		from
# # 			`tab{voucher_type}`
# # 		where
# # 			{party_type} = %s
# # 			and docstatus = 1
# # 			and company = %s
# # 			and status != "Closed"
# # 			and if({rounded_total_field}, {rounded_total_field}, {grand_total_field}) > advance_paid
# # 			and abs(100 - per_billed) > 0.01
# # 			{condition}
# # 		order by
# # 			transaction_date, name
# # 	""".format(
# # 			**{
# # 				"rounded_total_field": rounded_total_field,
# # 				"grand_total_field": grand_total_field,
# # 				"voucher_type": voucher_type,
# # 				"party_type": scrub(party_type),
# # 				"condition": condition,
# # 			}
# # 		),
# # 		(party, company),
# # 		as_dict=True,
# # 	)

# # 	order_list = []
# # 	for d in orders:
# # 		if (
# # 			filters
# # 			and filters.get("outstanding_amt_greater_than")
# # 			and filters.get("outstanding_amt_less_than")
# # 			and not (
# # 				flt(filters.get("outstanding_amt_greater_than"))
# # 				<= flt(d.outstanding_amount)
# # 				<= flt(filters.get("outstanding_amt_less_than"))
# # 			)
# # 		):
# # 			continue

# # 		d["voucher_type"] = voucher_type
# # 		# This assumes that the exchange rate required is the one in the SO
# # 		d["exchange_rate"] = get_exchange_rate(party_account_currency, company_currency, posting_date)
# # 		order_list.append(d)

# # 	return order_list


# # def get_negative_outstanding_invoices(
# # 	party_type,
# # 	party,
# # 	party_account,
# # 	party_account_currency,
# # 	company_currency,
# # 	cost_center=None,
# # 	condition=None,
# # ):
# # 	if party_type not in ["Customer", "Supplier"]:
# # 		return []
# # 	voucher_type = "Sales Invoice" if party_type == "Customer" else "Purchase Invoice"
# # 	account = "debit_to" if voucher_type == "Sales Invoice" else "credit_to"
# # 	supplier_condition = ""
# # 	if voucher_type == "Purchase Invoice":
# # 		supplier_condition = "and (release_date is null or release_date <= CURRENT_DATE)"
# # 	if party_account_currency == company_currency:
# # 		grand_total_field = "base_grand_total"
# # 		rounded_total_field = "base_rounded_total"
# # 	else:
# # 		grand_total_field = "grand_total"
# # 		rounded_total_field = "rounded_total"

# # 	return frappe.db.sql(
# # 		"""
# # 		select
# # 			"{voucher_type}" as voucher_type, name as voucher_no, {account} as account,
# # 			if({rounded_total_field}, {rounded_total_field}, {grand_total_field}) as invoice_amount,
# # 			outstanding_amount, posting_date,
# # 			due_date, conversion_rate as exchange_rate
# # 		from
# # 			`tab{voucher_type}`
# # 		where
# # 			{party_type} = %s and {party_account} = %s and docstatus = 1 and
# # 			outstanding_amount < 0
# # 			{supplier_condition}
# # 			{condition}
# # 		order by
# # 			posting_date, name
# # 		""".format(
# # 			**{
# # 				"supplier_condition": supplier_condition,
# # 				"condition": condition,
# # 				"rounded_total_field": rounded_total_field,
# # 				"grand_total_field": grand_total_field,
# # 				"voucher_type": voucher_type,
# # 				"party_type": scrub(party_type),
# # 				"party_account": "debit_to" if party_type == "Customer" else "credit_to",
# # 				"cost_center": cost_center,
# # 				"account": account,
# # 			}
# # 		),
# # 		(party, party_account),
# # 		as_dict=True,
# # 	)


# # @frappe.whitelist()
# # def get_party_details(company, party_type, party, date, cost_center=None):
# # 	bank_account = ""
# # 	party_bank_account = ""

# # 	if not frappe.db.exists(party_type, party):
# # 		frappe.throw(_("{0} {1} does not exist").format(_(party_type), party))

# # 	party_account = get_party_account(party_type, party, company)
# # 	account_currency = get_account_currency(party_account)
# # 	account_balance = get_balance_on(party_account, date, cost_center=cost_center)
# # 	_party_name = "title" if party_type == "Shareholder" else party_type.lower() + "_name"
# # 	party_name = frappe.db.get_value(party_type, party, _party_name)
# # 	party_balance = get_balance_on(
# # 		party_type=party_type, party=party, company=company, cost_center=cost_center
# # 	)
# # 	if party_type in ["Customer", "Supplier"]:
# # 		party_bank_account = get_party_bank_account(party_type, party)
# # 		bank_account = get_default_company_bank_account(company, party_type, party)

# # 	return {
# # 		"party_account": party_account,
# # 		"party_name": party_name,
# # 		"party_account_currency": account_currency,
# # 		"party_balance": party_balance,
# # 		"account_balance": account_balance,
# # 		"party_bank_account": party_bank_account,
# # 		"bank_account": bank_account,
# # 	}


# # @frappe.whitelist()
# # def get_account_details(account, date, cost_center=None):
# #     frappe.has_permission("Advance Sales Invoice", throw=True)

# #     account_list = frappe.get_list("Account", {"name": account}, reference_doctype="Advance Sales Invoice", limit=1)

# #     if not account_list:
# #         frappe.throw(_("Account: {0} is not permitted under Advance Sales Invoice").format(account))

# #     account_balance = get_balance_on(account, date, cost_center=cost_center, ignore_account_permission=True)

# #     return frappe._dict(
# #         {
# #             "account_currency": get_account_currency(account),
# #             "account_balance": account_balance,
# #             "account_type": frappe.get_cached_value("Account", account, "account_type"),
# #         }
# #     )


# # @frappe.whitelist()
# # def get_company_defaults(company):
# # 	fields = ["write_off_account", "exchange_gain_loss_account", "cost_center"]
# # 	return frappe.get_cached_value("Company", company, fields, as_dict=1)


# # def get_outstanding_on_journal_entry(voucher_no, party_type, party):
# # 	ple = frappe.qb.DocType("Payment Ledger Entry")

# # 	outstanding = (
# # 		frappe.qb.from_(ple)
# # 		.select(Sum(ple.amount_in_account_currency))
# # 		.where(
# # 			(ple.against_voucher_no == voucher_no)
# # 			& (ple.party_type == party_type)
# # 			& (ple.party == party)
# # 			& (ple.delinked == 0)
# # 		)
# # 	).run()

# # 	outstanding_amount = outstanding[0][0] if outstanding else 0

# # 	total = (
# # 		frappe.qb.from_(ple)
# # 		.select(Sum(ple.amount_in_account_currency))
# # 		.where(
# # 			(ple.voucher_no == voucher_no)
# # 			& (ple.party_type == party_type)
# # 			& (ple.party == party)
# # 			& (ple.delinked == 0)
# # 		)
# # 	).run()

# # 	total_amount = total[0][0] if total else 0

# # 	return outstanding_amount, total_amount


# # @frappe.whitelist()
# # def get_reference_details(
# # 	reference_doctype, reference_name, party_account_currency, party_type=None, party=None
# # ):
# # 	total_amount = outstanding_amount = exchange_rate = account = None

# # 	ref_doc = frappe.get_doc(reference_doctype, reference_name)
# # 	company_currency = ref_doc.get("company_currency") or erpnext.get_company_currency(ref_doc.company)

# # 	# Only applies for Reverse Payment Entries
# # 	account_type = None
# # 	payment_type = None

# # 	if reference_doctype == "Dunning":
# # 		total_amount = outstanding_amount = ref_doc.get("dunning_amount")
# # 		exchange_rate = 1

# # 	elif reference_doctype == "Journal Entry" and ref_doc.docstatus == 1:
# # 		if ref_doc.multi_currency:
# # 			exchange_rate = get_exchange_rate(party_account_currency, company_currency, ref_doc.posting_date)
# # 		else:
# # 			exchange_rate = 1
# # 			outstanding_amount, total_amount = get_outstanding_on_journal_entry(
# # 				reference_name, party_type, party
# # 			)

# # 	elif reference_doctype == "Payment Entry":
# # 		if reverse_payment_details := frappe.db.get_all(
# # 			"Payment Entry",
# # 			filters={"name": reference_name},
# # 			fields=["payment_type", "party_type"],
# # 		)[0]:
# # 			payment_type = reverse_payment_details.payment_type
# # 			account_type = frappe.db.get_value(
# # 				"Party Type", reverse_payment_details.party_type, "account_type"
# # 			)
# # 		exchange_rate = 1

# # 	elif reference_doctype != "Journal Entry":
# # 		if not total_amount:
# # 			if party_account_currency == company_currency:
# # 				# for handling cases that don't have multi-currency (base field)
# # 				total_amount = (
# # 					ref_doc.get("base_rounded_total")
# # 					or ref_doc.get("rounded_total")
# # 					or ref_doc.get("base_grand_total")
# # 					or ref_doc.get("grand_total")
# # 				)
# # 				exchange_rate = 1
# # 			else:
# # 				total_amount = ref_doc.get("rounded_total") or ref_doc.get("grand_total")
# # 		if not exchange_rate:
# # 			# Get the exchange rate from the original ref doc
# # 			# or get it based on the posting date of the ref doc.
# # 			exchange_rate = ref_doc.get("conversion_rate") or get_exchange_rate(
# # 				party_account_currency, company_currency, ref_doc.posting_date
# # 			)

# # 		if reference_doctype in ("Sales Invoice", "Purchase Invoice"):
# # 			outstanding_amount = ref_doc.get("outstanding_amount")
# # 			account = (
# # 				ref_doc.get("debit_to") if reference_doctype == "Sales Invoice" else ref_doc.get("credit_to")
# # 			)
# # 		else:
# # 			outstanding_amount = flt(total_amount) - flt(ref_doc.get("advance_paid"))

# # 		if reference_doctype in ["Sales Order", "Purchase Order"]:
# # 			party_type = "Customer" if reference_doctype == "Sales Order" else "Supplier"
# # 			party_field = "customer" if reference_doctype == "Sales Order" else "supplier"
# # 			party = ref_doc.get(party_field)
# # 			account = get_party_account(party_type, party, ref_doc.company)
# # 	else:
# # 		# Get the exchange rate based on the posting date of the ref doc.
# # 		exchange_rate = get_exchange_rate(party_account_currency, company_currency, ref_doc.posting_date)

# # 	res = frappe._dict(
# # 		{
# # 			"due_date": ref_doc.get("due_date"),
# # 			"total_amount": flt(total_amount),
# # 			"outstanding_amount": flt(outstanding_amount),
# # 			"exchange_rate": flt(exchange_rate),
# # 			"bill_no": ref_doc.get("bill_no"),
# # 			"account_type": account_type,
# # 			"payment_type": payment_type,
# # 		}
# # 	)
# # 	if account:
# # 		res.update({"account": account})
# # 	return res


# # @frappe.whitelist()
# # def get_payment_entry(
# #     dt,
# #     dn,
# #     party_amount=None,
# #     bank_account=None,
# #     bank_amount=None,
# #     party_type=None,
# #     payment_type=None,
# #     reference_date=None,
# #     ignore_permissions=False,
# #     created_from_payment_request=False,
# # ):
# # 	doc = frappe.get_doc(dt, dn)
# # 	frappe.msgprint("py")
# # 	over_billing_allowance = frappe.db.get_single_value("Accounts Settings", "over_billing_allowance")
# # 	if dt in ("Sales Order", "Purchase Order") and flt(doc.per_billed, 2) >= (100.0 + over_billing_allowance):
# # 		frappe.throw(_("Can only make payment against unbilled {0}").format(_(dt)))

# # 	if not party_type:
# # 		party_type = set_party_type(dt)

# # 	party_account = set_party_account(dt, dn, doc, party_type)
# # 	party_account_currency = set_party_account_currency(dt, party_account, doc)

# # 	if not payment_type:
# # 		payment_type = set_payment_type(dt, doc)

# # 	grand_total, outstanding_amount = set_grand_total_and_outstanding_amount(
# # 		party_amount, dt, party_account_currency, doc
# # 	)

# # 	# bank or cash
# # 	bank = get_bank_cash_account(doc, bank_account)

# # 	# if default bank or cash account is not set in company master and party has default company bank account, fetch it
# # 	if party_type in ["Customer", "Supplier"] and not bank:
# # 		party_bank_account = get_party_bank_account(party_type, doc.get(scrub(party_type)))
# # 		if party_bank_account:
# # 			account = frappe.db.get_value("Bank Account", party_bank_account, "account")
# # 			bank = get_bank_cash_account(doc, account)

# # 	paid_amount, received_amount = set_paid_amount_and_received_amount(
# # 		dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc
# # 	)

# # 	reference_date = getdate(reference_date)
# # 	paid_amount, received_amount, discount_amount, valid_discounts = apply_early_payment_discount(
# # 		paid_amount, received_amount, doc, party_account_currency, reference_date
# # 	)

# # 	pe = frappe.new_doc("Advance Sales Invoice")
# # 	pe.payment_type = payment_type
# # 	pe.company = doc.company
# # 	pe.cost_center = doc.get("cost_center")
# # 	pe.posting_date = nowdate()
# # 	pe.reference_date = reference_date
# # 	pe.mode_of_payment = doc.get("mode_of_payment")
# # 	pe.party_type = party_type
# # 	pe.party = doc.get(scrub(party_type))
# # 	pe.contact_person = doc.get("contact_person")
# # 	pe.contact_email = doc.get("contact_email")
# # 	pe.ensure_supplier_is_not_blocked()

# # 	pe.paid_from = party_account if payment_type == "Receive" else bank.account
# # 	pe.paid_to = party_account if payment_type == "Pay" else bank.account
# # 	pe.paid_from_account_currency = (
# # 		party_account_currency if payment_type == "Receive" else bank.account_currency
# # 	)
# # 	pe.paid_to_account_currency = party_account_currency if payment_type == "Pay" else bank.account_currency
# # 	pe.paid_amount = paid_amount
# # 	pe.received_amount = received_amount
# # 	pe.letter_head = doc.get("letter_head")
# # 	pe.bank_account = frappe.db.get_value("Bank Account", {"is_company_account": 1, "is_default": 1}, "name")

# # 	if dt in ["Purchase Order", "Sales Order", "Sales Invoice", "Purchase Invoice"]:
# # 		pe.project = doc.get("project") or reduce(
# # 			lambda prev, cur: prev or cur, [x.get("project") for x in doc.get("items")], None
# # 		)  # get first non-empty project from items

# # 	if pe.party_type in ["Customer", "Supplier"]:
# # 		bank_account = get_party_bank_account(pe.party_type, pe.party)
# # 		pe.set("party_bank_account", bank_account)
# # 		pe.set_bank_account_data()

# # 	# only Purchase Invoice can be blocked individually
# # 	if doc.doctype == "Purchase Invoice" and doc.invoice_is_blocked():
# # 		frappe.msgprint(_("{0} is on hold till {1}").format(doc.name, doc.release_date))
# # 	else:
# # 		if doc.doctype in (
# # 			"Sales Invoice",
# # 			"Purchase Invoice",
# # 			"Purchase Order",
# # 			"Sales Order",
# # 		) and frappe.get_cached_value(
# # 			"Payment Terms Template",
# # 			doc.payment_terms_template,
# # 			"allocate_payment_based_on_payment_terms",
# # 		):
# # 			for reference in get_reference_as_per_payment_terms(
# # 				doc.payment_schedule, dt, dn, doc, grand_total, outstanding_amount, party_account_currency
# # 			):
# # 				pe.append("references", reference)
# # 		else:
# # 			if dt == "Dunning":
# # 				for overdue_payment in doc.overdue_payments:
# # 					pe.append(
# # 						"references",
# # 						{
# # 							"reference_doctype": "Sales Invoice",
# # 							"reference_name": overdue_payment.sales_invoice,
# # 							"payment_term": overdue_payment.payment_term,
# # 							"due_date": overdue_payment.due_date,
# # 							"total_amount": overdue_payment.outstanding,
# # 							"outstanding_amount": overdue_payment.outstanding,
# # 							"allocated_amount": overdue_payment.outstanding,
# # 						},
# # 					)

# # 				pe.append(
# # 					"deductions",
# # 					{
# # 						"account": doc.income_account,
# # 						"cost_center": doc.cost_center,
# # 						"amount": -1 * doc.dunning_amount,
# # 						"description": _("Interest and/or dunning fee"),
# # 					},
# # 				)
# # 			else:
# # 				pe.append(
# # 					"references",
# # 					{
# # 						"reference_doctype": dt,
# # 						"reference_name": dn,
# # 						"bill_no": doc.get("bill_no"),
# # 						"due_date": doc.get("due_date"),
# # 						"total_amount": grand_total,
# # 						"outstanding_amount": outstanding_amount,
# # 						"allocated_amount": outstanding_amount,
# # 					},
# # 				)

# # 	pe.setup_party_account_field()
# # 	pe.set_missing_values()
# # 	pe.set_missing_ref_details()

# # 	update_accounting_dimensions(pe, doc)

# # 	if party_account and bank:
# # 		if discount_amount:
# # 			base_total_discount_loss = 0
# # 			if frappe.db.get_single_value("Accounts Settings", "book_tax_discount_loss"):
# # 				base_total_discount_loss = split_early_payment_discount_loss(pe, doc, valid_discounts)

# # 			set_pending_discount_loss(
# # 				pe, doc, discount_amount, base_total_discount_loss, party_account_currency
# # 			)

# # 		pe.set_exchange_rate(ref_doc=doc)
# # 		pe.set_amounts()

# # 	# If PE is created from PR directly, then no need to find open PRs for the references
# # 	if not created_from_payment_request:
# # 		allocate_open_payment_requests_to_references(pe.references, pe.precision("paid_amount"))

# # 	return pe


# # def get_open_payment_requests_for_references(references=None):
# # 	"""
# # 	Fetch all unpaid Payment Requests for the references. \n
# # 	        - Each reference can have multiple Payment Requests. \n

# # 	Example: {("Sales Invoice", "SINV-00001"): {"PREQ-00001": 1000, "PREQ-00002": 2000}}
# # 	"""
# # 	if not references:
# # 		return

# # 	refs = {
# # 		(row.reference_doctype, row.reference_name)
# # 		for row in references
# # 		if row.reference_doctype and row.reference_name and row.allocated_amount
# # 	}

# # 	if not refs:
# # 		return

# # 	PR = frappe.qb.DocType("Payment Request")

# # 	response = (
# # 		frappe.qb.from_(PR)
# # 		.select(PR.name, PR.reference_doctype, PR.reference_name, PR.outstanding_amount)
# # 		.where(Tuple(PR.reference_doctype, PR.reference_name).isin(list(refs)))
# # 		.where(PR.status != "Paid")
# # 		.where(PR.docstatus == 1)
# # 		.where(PR.outstanding_amount > 0)  # to avoid old PRs with 0 outstanding amount
# # 		.orderby(Coalesce(PR.transaction_date, PR.creation), order=frappe.qb.asc)
# # 	).run(as_dict=True)

# # 	if not response:
# # 		return

# # 	reference_payment_requests = {}

# # 	for row in response:
# # 		key = (row.reference_doctype, row.reference_name)

# # 		if key not in reference_payment_requests:
# # 			reference_payment_requests[key] = {row.name: row.outstanding_amount}
# # 		else:
# # 			reference_payment_requests[key][row.name] = row.outstanding_amount

# # 	return reference_payment_requests


# # def allocate_open_payment_requests_to_references(references=None, precision=None):
# # 	"""
# # 	Allocate unpaid Payment Requests to the references. \n
# # 	---
# # 	- Allocation based on below factors
# # 	    - Reference Allocated Amount
# # 	    - Reference Outstanding Amount (With Payment Terms or without Payment Terms)
# # 	    - Reference Payment Request's outstanding amount
# # 	---
# # 	- Allocation based on below scenarios
# # 	    - Reference's Allocated Amount == Payment Request's Outstanding Amount
# # 	        - Allocate the Payment Request to the reference
# # 	        - This PR will not be allocated further
# # 	    - Reference's Allocated Amount < Payment Request's Outstanding Amount
# # 	        - Allocate the Payment Request to the reference
# # 	        - Reduce the PR's outstanding amount by the allocated amount
# # 	        - This PR can be allocated further
# # 	    - Reference's Allocated Amount > Payment Request's Outstanding Amount
# # 	        - Allocate the Payment Request to the reference
# # 	        - Reduce Allocated Amount of the reference by the PR's outstanding amount
# # 	        - Create a new row for the remaining amount until the Allocated Amount is 0
# # 	            - Allocate PR if available
# # 	---
# # 	- Note:
# # 	    - Priority is given to the first Payment Request of respective references.
# # 	    - Single Reference can have multiple rows.
# # 	        - With Payment Terms or without Payment Terms
# # 	        - With Payment Request or without Payment Request
# # 	"""
# # 	if not references:
# # 		return

# # 	# get all unpaid payment requests for the references
# # 	references_open_payment_requests = get_open_payment_requests_for_references(references)

# # 	if not references_open_payment_requests:
# # 		return

# # 	if not precision:
# # 		precision = references[0].precision("allocated_amount")

# # 	# to manage new rows
# # 	row_number = 1
# # 	MOVE_TO_NEXT_ROW = 1
# # 	TO_SKIP_NEW_ROW = 2

# # 	while row_number <= len(references):
# # 		row = references[row_number - 1]
# # 		reference_key = (row.reference_doctype, row.reference_name)

# # 		# update the idx to maintain the order
# # 		row.idx = row_number

# # 		# unpaid payment requests for the reference
# # 		reference_payment_requests = references_open_payment_requests.get(reference_key)

# # 		if not reference_payment_requests:
# # 			row_number += MOVE_TO_NEXT_ROW  # to move to next reference row
# # 			continue

# # 		# get the first payment request and its outstanding amount
# # 		payment_request, pr_outstanding_amount = next(iter(reference_payment_requests.items()))
# # 		allocated_amount = row.allocated_amount

# # 		# allocate the payment request to the reference and PR's outstanding amount
# # 		row.payment_request = payment_request

# # 		if pr_outstanding_amount == allocated_amount:
# # 			del reference_payment_requests[payment_request]
# # 			row_number += MOVE_TO_NEXT_ROW

# # 		elif pr_outstanding_amount > allocated_amount:
# # 			# reduce the outstanding amount of the payment request
# # 			reference_payment_requests[payment_request] -= allocated_amount
# # 			row_number += MOVE_TO_NEXT_ROW

# # 		else:
# # 			# split the reference row to allocate the remaining amount
# # 			del reference_payment_requests[payment_request]
# # 			row.allocated_amount = pr_outstanding_amount
# # 			allocated_amount = flt(allocated_amount - pr_outstanding_amount, precision)

# # 			# set the remaining amount to the next row
# # 			while allocated_amount:
# # 				# create a new row for the remaining amount
# # 				new_row = frappe.copy_doc(row)
# # 				references.insert(row_number, new_row)

# # 				# get the first payment request and its outstanding amount
# # 				payment_request, pr_outstanding_amount = next(
# # 					iter(reference_payment_requests.items()), (None, None)
# # 				)

# # 				# update new row
# # 				new_row.idx = row_number + 1
# # 				new_row.payment_request = payment_request
# # 				new_row.allocated_amount = min(
# # 					pr_outstanding_amount if pr_outstanding_amount else allocated_amount, allocated_amount
# # 				)

# # 				if not payment_request or not pr_outstanding_amount:
# # 					row_number += TO_SKIP_NEW_ROW
# # 					break

# # 				elif pr_outstanding_amount == allocated_amount:
# # 					del reference_payment_requests[payment_request]
# # 					row_number += TO_SKIP_NEW_ROW
# # 					break

# # 				elif pr_outstanding_amount > allocated_amount:
# # 					reference_payment_requests[payment_request] -= allocated_amount
# # 					row_number += TO_SKIP_NEW_ROW
# # 					break

# # 				else:
# # 					allocated_amount = flt(allocated_amount - pr_outstanding_amount, precision)
# # 					del reference_payment_requests[payment_request]
# # 					row_number += MOVE_TO_NEXT_ROW


# # def update_accounting_dimensions(pe, doc):
# # 	"""
# # 	Updates accounting dimensions in Payment Entry based on the accounting dimensions in the reference document
# # 	"""
# # 	from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
# # 		get_accounting_dimensions,
# # 	)

# # 	for dimension in get_accounting_dimensions():
# # 		pe.set(dimension, doc.get(dimension))


# # def get_bank_cash_account(doc, bank_account):
# # 	bank = get_default_bank_cash_account(
# # 		doc.company, "Bank", mode_of_payment=doc.get("mode_of_payment"), account=bank_account
# # 	)

# # 	if not bank:
# # 		bank = get_default_bank_cash_account(
# # 			doc.company, "Cash", mode_of_payment=doc.get("mode_of_payment"), account=bank_account
# # 		)

# # 	return bank


# # def set_party_type(dt):
# # 	if dt in ("Sales Invoice", "Sales Order", "Dunning"):
# # 		party_type = "Customer"
# # 	elif dt in ("Purchase Invoice", "Purchase Order"):
# # 		party_type = "Supplier"
# # 	return party_type


# # def set_party_account(dt, dn, doc, party_type):
# # 	if dt == "Sales Invoice":
# # 		party_account = get_party_account_based_on_invoice_discounting(dn) or doc.debit_to
# # 	elif dt == "Purchase Invoice":
# # 		party_account = doc.credit_to
# # 	else:
# # 		party_account = get_party_account(party_type, doc.get(party_type.lower()), doc.company)
# # 	return party_account


# # def set_party_account_currency(dt, party_account, doc):
# # 	if dt not in ("Sales Invoice", "Purchase Invoice"):
# # 		party_account_currency = get_account_currency(party_account)
# # 	else:
# # 		party_account_currency = doc.get("party_account_currency") or get_account_currency(party_account)
# # 	return party_account_currency


# # def set_payment_type(dt, doc):
# # 	if (
# # 		(dt == "Sales Order" or (dt == "Sales Invoice" and doc.outstanding_amount > 0))
# # 		or (dt == "Purchase Invoice" and doc.outstanding_amount < 0)
# # 		or dt == "Dunning"
# # 	):
# # 		payment_type = "Receive"
# # 	else:
# # 		payment_type = "Pay"
# # 	return payment_type


# # def set_grand_total_and_outstanding_amount(party_amount, dt, party_account_currency, doc):
# # 	grand_total = outstanding_amount = 0
# # 	if party_amount:
# # 		grand_total = outstanding_amount = party_amount
# # 	elif dt in ("Sales Invoice", "Purchase Invoice"):
# # 		if party_account_currency == doc.company_currency:
# # 			grand_total = doc.base_rounded_total or doc.base_grand_total
# # 		else:
# # 			grand_total = doc.rounded_total or doc.grand_total
# # 		outstanding_amount = doc.outstanding_amount
# # 	elif dt == "Dunning":
# # 		grand_total = doc.grand_total
# # 		outstanding_amount = doc.grand_total
# # 	else:
# # 		if party_account_currency == doc.company_currency:
# # 			grand_total = flt(doc.get("base_rounded_total") or doc.get("base_grand_total"))
# # 		else:
# # 			grand_total = flt(doc.get("rounded_total") or doc.get("grand_total"))
# # 		outstanding_amount = doc.get("outstanding_amount") or (grand_total - flt(doc.advance_paid))
# # 	return grand_total, outstanding_amount


# # def set_paid_amount_and_received_amount(
# # 	dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc
# # ):
# # 	paid_amount = received_amount = 0
# # 	if party_account_currency == bank.account_currency:
# # 		paid_amount = received_amount = abs(outstanding_amount)
# # 	else:
# # 		company_currency = frappe.get_cached_value("Company", doc.get("company"), "default_currency")
# # 		if payment_type == "Receive":
# # 			paid_amount = abs(outstanding_amount)
# # 			if bank_amount:
# # 				received_amount = bank_amount
# # 			else:
# # 				if bank and company_currency != bank.account_currency:
# # 					received_amount = paid_amount / doc.get("conversion_rate", 1)
# # 				else:
# # 					received_amount = paid_amount * doc.get("conversion_rate", 1)
# # 		else:
# # 			received_amount = abs(outstanding_amount)
# # 			if bank_amount:
# # 				paid_amount = bank_amount
# # 			else:
# # 				if bank and company_currency != bank.account_currency:
# # 					paid_amount = received_amount / doc.get("conversion_rate", 1)
# # 				else:
# # 					# if party account currency and bank currency is different then populate paid amount as well
# # 					paid_amount = received_amount * doc.get("conversion_rate", 1)

# # 	return paid_amount, received_amount


# # def apply_early_payment_discount(paid_amount, received_amount, doc, party_account_currency, reference_date):
# # 	total_discount = 0
# # 	valid_discounts = []
# # 	eligible_for_payments = ["Sales Order", "Sales Invoice", "Purchase Order", "Purchase Invoice"]
# # 	has_payment_schedule = hasattr(doc, "payment_schedule") and doc.payment_schedule
# # 	is_multi_currency = party_account_currency != doc.company_currency

# # 	if doc.doctype in eligible_for_payments and has_payment_schedule:
# # 		for term in doc.payment_schedule:
# # 			if not term.discounted_amount and term.discount and reference_date <= term.discount_date:
# # 				if term.discount_type == "Percentage":
# # 					grand_total = doc.get("grand_total") if is_multi_currency else doc.get("base_grand_total")
# # 					discount_amount = flt(grand_total) * (term.discount / 100)
# # 				else:
# # 					discount_amount = term.discount

# # 				# if accounting is done in the same currency, paid_amount = received_amount
# # 				conversion_rate = doc.get("conversion_rate", 1) if is_multi_currency else 1
# # 				discount_amount_in_foreign_currency = discount_amount * conversion_rate

# # 				if doc.doctype == "Sales Invoice":
# # 					paid_amount -= discount_amount
# # 					received_amount -= discount_amount_in_foreign_currency
# # 				else:
# # 					received_amount -= discount_amount
# # 					paid_amount -= discount_amount_in_foreign_currency

# # 				valid_discounts.append({"type": term.discount_type, "discount": term.discount})
# # 				total_discount += discount_amount

# # 		if total_discount:
# # 			currency = doc.get("currency") if is_multi_currency else doc.company_currency
# # 			money = frappe.utils.fmt_money(total_discount, currency=currency)
# # 			frappe.msgprint(_("Discount of {} applied as per Payment Term").format(money), alert=1)

# # 	return paid_amount, received_amount, total_discount, valid_discounts


# # def set_pending_discount_loss(pe, doc, discount_amount, base_total_discount_loss, party_account_currency):
# # 	# If multi-currency, get base discount amount to adjust with base currency deductions/losses
# # 	if party_account_currency != doc.company_currency:
# # 		discount_amount = discount_amount * doc.get("conversion_rate", 1)

# # 	# Avoid considering miniscule losses
# # 	discount_amount = flt(discount_amount - base_total_discount_loss, doc.precision("grand_total"))

# # 	# Set base discount amount (discount loss/pending rounding loss) in deductions
# # 	if discount_amount > 0.0:
# # 		positive_negative = -1 if pe.payment_type == "Pay" else 1

# # 		# If tax loss booking is enabled, pending loss will be rounding loss.
# # 		# Otherwise it will be the total discount loss.
# # 		book_tax_loss = frappe.db.get_single_value("Accounts Settings", "book_tax_discount_loss")
# # 		account_type = "round_off_account" if book_tax_loss else "default_discount_account"

# # 		pe.append(
# # 			"deductions",
# # 			{
# # 				"account": frappe.get_cached_value("Company", pe.company, account_type),
# # 				"cost_center": pe.cost_center
# # 				or frappe.get_cached_value("Company", pe.company, "cost_center"),
# # 				"amount": discount_amount * positive_negative,
# # 			},
# # 		)


# # def split_early_payment_discount_loss(pe, doc, valid_discounts) -> float:
# # 	"""Split early payment discount into Income Loss & Tax Loss."""
# # 	total_discount_percent = get_total_discount_percent(doc, valid_discounts)

# # 	if not total_discount_percent:
# # 		return 0.0

# # 	base_loss_on_income = add_income_discount_loss(pe, doc, total_discount_percent)
# # 	base_loss_on_taxes = add_tax_discount_loss(pe, doc, total_discount_percent)

# # 	# Round off total loss rather than individual losses to reduce rounding error
# # 	return flt(base_loss_on_income + base_loss_on_taxes, doc.precision("grand_total"))


# # def get_total_discount_percent(doc, valid_discounts) -> float:
# # 	"""Get total percentage and amount discount applied as a percentage."""
# # 	total_discount_percent = (
# # 		sum(discount.get("discount") for discount in valid_discounts if discount.get("type") == "Percentage")
# # 		or 0.0
# # 	)

# # 	# Operate in percentages only as it makes the income & tax split easier
# # 	total_discount_amount = (
# # 		sum(discount.get("discount") for discount in valid_discounts if discount.get("type") == "Amount")
# # 		or 0.0
# # 	)

# # 	if total_discount_amount:
# # 		discount_percentage = (total_discount_amount / doc.get("grand_total")) * 100
# # 		total_discount_percent += discount_percentage
# # 		return total_discount_percent

# # 	return total_discount_percent


# # def add_income_discount_loss(pe, doc, total_discount_percent) -> float:
# # 	"""Add loss on income discount in base currency."""
# # 	precision = doc.precision("total")
# # 	base_loss_on_income = doc.get("base_total") * (total_discount_percent / 100)

# # 	pe.append(
# # 		"deductions",
# # 		{
# # 			"account": frappe.get_cached_value("Company", pe.company, "default_discount_account"),
# # 			"cost_center": pe.cost_center or frappe.get_cached_value("Company", pe.company, "cost_center"),
# # 			"amount": flt(base_loss_on_income, precision),
# # 		},
# # 	)

# # 	return base_loss_on_income  # Return loss without rounding


# # def add_tax_discount_loss(pe, doc, total_discount_percentage) -> float:
# # 	"""Add loss on tax discount in base currency."""
# # 	tax_discount_loss = {}
# # 	base_total_tax_loss = 0
# # 	precision = doc.precision("tax_amount_after_discount_amount", "taxes")

# # 	# The same account head could be used more than once
# # 	for tax in doc.get("taxes", []):
# # 		base_tax_loss = tax.get("base_tax_amount_after_discount_amount") * (total_discount_percentage / 100)

# # 		account = tax.get("account_head")
# # 		if not tax_discount_loss.get(account):
# # 			tax_discount_loss[account] = base_tax_loss
# # 		else:
# # 			tax_discount_loss[account] += base_tax_loss

# # 	for account, loss in tax_discount_loss.items():
# # 		base_total_tax_loss += loss
# # 		if loss == 0.0:
# # 			continue

# # 		pe.append(
# # 			"deductions",
# # 			{
# # 				"account": account,
# # 				"cost_center": pe.cost_center
# # 				or frappe.get_cached_value("Company", pe.company, "cost_center"),
# # 				"amount": flt(loss, precision),
# # 			},
# # 		)

# # 	return base_total_tax_loss  # Return loss without rounding


# # def get_reference_as_per_payment_terms(
# # 	payment_schedule, dt, dn, doc, grand_total, outstanding_amount, party_account_currency
# # ):
# # 	references = []
# # 	is_multi_currency_acc = (doc.currency != doc.company_currency) and (
# # 		party_account_currency != doc.company_currency
# # 	)

# # 	for payment_term in payment_schedule:
# # 		payment_term_outstanding = flt(
# # 			payment_term.payment_amount - payment_term.paid_amount, payment_term.precision("payment_amount")
# # 		)
# # 		if not is_multi_currency_acc:
# # 			# If accounting is done in company currency for multi-currency transaction
# # 			payment_term_outstanding = flt(
# # 				payment_term_outstanding * doc.get("conversion_rate"),
# # 				payment_term.precision("payment_amount"),
# # 			)

# # 		if payment_term_outstanding:
# # 			references.append(
# # 				{
# # 					"reference_doctype": dt,
# # 					"reference_name": dn,
# # 					"bill_no": doc.get("bill_no"),
# # 					"due_date": doc.get("due_date"),
# # 					"total_amount": grand_total,
# # 					"outstanding_amount": outstanding_amount,
# # 					"payment_term_outstanding": payment_term_outstanding,
# # 					"payment_term": payment_term.payment_term,
# # 					"allocated_amount": payment_term_outstanding,
# # 				}
# # 			)

# # 	return references


# # def get_paid_amount(dt, dn, party_type, party, account, due_date):
# # 	if party_type == "Customer":
# # 		dr_or_cr = "credit_in_account_currency - debit_in_account_currency"
# # 	else:
# # 		dr_or_cr = "debit_in_account_currency - credit_in_account_currency"

# # 	paid_amount = frappe.db.sql(
# # 		f"""
# # 		select ifnull(sum({dr_or_cr}), 0) as paid_amount
# # 		from `tabGL Entry`
# # 		where against_voucher_type = %s
# # 			and against_voucher = %s
# # 			and party_type = %s
# # 			and party = %s
# # 			and account = %s
# # 			and due_date = %s
# # 			and {dr_or_cr} > 0
# # 	""",
# # 		(dt, dn, party_type, party, account, due_date),
# # 	)

# # 	return paid_amount[0][0] if paid_amount else 0


# # @frappe.whitelist()
# # def get_party_and_account_balance(
# # 	company, date, paid_from=None, paid_to=None, ptype=None, pty=None, cost_center=None
# # ):
# # 	return frappe._dict(
# # 		{
# # 			"party_balance": get_balance_on(party_type=ptype, party=pty, cost_center=cost_center),
# # 			"paid_from_account_balance": get_balance_on(paid_from, date, cost_center=cost_center),
# # 			"paid_to_account_balance": get_balance_on(paid_to, date=date, cost_center=cost_center),
# # 		}
# # 	)


# # @frappe.whitelist()
# # def make_payment_order(source_name, target_doc=None):
# #     from frappe.model.mapper import get_mapped_doc

# #     def set_missing_values(source, target):
# #         target.payment_order_type = "Advance Sales Invoice"
# #         target.append(
# #             "references",
# #             dict(
# #                 reference_doctype="Advance Sales Invoice",
# #                 reference_name=source.name,
# #                 bank_account=source.party_bank_account,
# #                 amount=source.paid_amount,
# #                 account=source.paid_to,
# #                 supplier=source.party,
# #                 mode_of_payment=source.mode_of_payment,
# #             ),
# #         )

# #     doclist = get_mapped_doc(
# #         "Advance Sales Invoice",
# #         source_name,
# #         {"Advance Sales Invoice": {"doctype": "Payment Order", "validation": {"docstatus": ["=", 1]}}},
# #         target_doc,
# #         set_missing_values,
# #     )

# #     return doclist


# # @erpnext.allow_regional
# # def add_regional_gl_entries(gl_entries, doc):
# # 	return



# # Copyright (c) 2025, Claudion and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document


# class AdvanceSalesInvoice(Document):
# 	frappe.msgprint("python loads")
# 	pass


import frappe
from frappe.model.document import Document


class AdvanceSalesInvoice(Document):
	def update_payment_schedule(self, cancel=0):
		invoice_payment_amount_map = {}
		invoice_paid_amount_map = {}

		for ref in self.get("references"):
			if ref.payment_term and ref.reference_name:
				key = (ref.payment_term, ref.reference_name, ref.reference_doctype)
				invoice_payment_amount_map.setdefault(key, 0.0)
				invoice_payment_amount_map[key] += ref.allocated_amount

				if not invoice_paid_amount_map.get(key):
					payment_schedule = frappe.get_all(
						"Payment Schedule",
						filters={"parent": ref.reference_name},
						fields=[
							"paid_amount",
							"payment_amount",
							"payment_term",
							"discount",
							"outstanding",
							"discount_type",
						],
					)
					for term in payment_schedule:
						invoice_key = (term.payment_term, ref.reference_name, ref.reference_doctype)
						invoice_paid_amount_map.setdefault(invoice_key, {})
						invoice_paid_amount_map[invoice_key]["outstanding"] = term.outstanding
						if not (term.discount_type and term.discount):
							continue

						if term.discount_type == "Percentage":
							invoice_paid_amount_map[invoice_key]["discounted_amt"] = ref.total_amount * (
								term.discount / 100
							)
						else:
							invoice_paid_amount_map[invoice_key]["discounted_amt"] = term.discount

		for idx, (key, allocated_amount) in enumerate(invoice_payment_amount_map.items(), 1):
			if not invoice_paid_amount_map.get(key):
				frappe.throw(_("Payment term {0} not used in {1}").format(key[0], key[1]))

			allocated_amount = self.get_allocated_amount_in_transaction_currency(
				allocated_amount, key[2], key[1]
			)

			outstanding = flt(invoice_paid_amount_map.get(key, {}).get("outstanding"))
			discounted_amt = flt(invoice_paid_amount_map.get(key, {}).get("discounted_amt"))

			if cancel:
				frappe.db.sql(
					"""
					UPDATE `tabPayment Schedule`
					SET
						paid_amount = `paid_amount` - %s,
						discounted_amount = `discounted_amount` - %s,
						outstanding = `outstanding` + %s
					WHERE parent = %s and payment_term = %s""",
					(allocated_amount - discounted_amt, discounted_amt, allocated_amount, key[1], key[0]),
				)
			else:
				if allocated_amount > outstanding:
					frappe.throw(
						_("Row #{0}: Cannot allocate more than {1} against payment term {2}").format(
							idx, fmt_money(outstanding), key[0]
						)
					)

				if allocated_amount and outstanding:
					frappe.db.sql(
						"""
						UPDATE `tabPayment Schedule`
						SET
							paid_amount = `paid_amount` + %s,
							discounted_amount = `discounted_amount` + %s,
							outstanding = `outstanding` - %s
						WHERE parent = %s and payment_term = %s""",
						(allocated_amount - discounted_amt, discounted_amt, allocated_amount, key[1], key[0]),
					)

	def get_allocated_amount_in_transaction_currency(
		self, allocated_amount, reference_doctype, reference_docname
	):
		"""
		Payment Entry could be in base currency while reference's payment schedule
		is always in transaction currency.
		E.g.
		* SI with base=INR and currency=USD
		* SI with payment schedule in USD
		* PE in INR (accounting done in base currency)
		"""
		ref_currency, ref_exchange_rate = frappe.db.get_value(
			reference_doctype, reference_docname, ["currency", "conversion_rate"]
		)
		is_single_currency = self.paid_from_account_currency == self.paid_to_account_currency
		# PE in different currency
		reference_is_multi_currency = self.paid_from_account_currency != ref_currency

		if not (is_single_currency and reference_is_multi_currency):
			return allocated_amount

		allocated_amount = flt(allocated_amount / ref_exchange_rate, self.precision("total_allocated_amount"))

		return allocated_amount

