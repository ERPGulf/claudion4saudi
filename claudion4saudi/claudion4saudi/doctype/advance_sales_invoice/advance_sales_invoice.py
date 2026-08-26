

from frappe.model.document import Document


import frappe
from frappe import _
from frappe.utils import flt
from frappe.utils.data import get_link_to_form

from erpnext.accounts.doctype.bank_account.bank_account import (
	get_bank_account_details,
)
from erpnext.accounts.doctype.payment_entry.payment_entry import (
	allocate_open_payment_requests_to_references,
	get_payment_request_outstanding_set_in_references,
	get_references_outstanding_amount,
)
from erpnext.setup.utils import get_exchange_rate




class AdvanceSalesInvoice(Document):
	pass


	def set_bank_account_data(self):
		if self.bank_account:
			bank_data = get_bank_account_details(self.bank_account)

			field = "paid_from" if self.payment_type == "Pay" else "paid_to"

			self.bank = bank_data.bank
			self.bank_account_no = bank_data.bank_account_no

			if not self.get(field):
				self.set(field, bank_data.account)


	def set_exchange_rate(self, ref_doc=None):
		self.set_source_exchange_rate(ref_doc)
		self.set_target_exchange_rate(ref_doc)

	def set_source_exchange_rate(self, ref_doc=None):
		if self.paid_from:
			
			if self.paid_from_account_currency == self.company_currency:
				self.source_exchange_rate = 1
			else:
				if ref_doc:
					if self.paid_from_account_currency == ref_doc.currency:
						self.source_exchange_rate = ref_doc.get("exchange_rate") or ref_doc.get(
							"conversion_rate"
						)

			if not self.source_exchange_rate:
				self.source_exchange_rate = get_exchange_rate(
					self.paid_from_account_currency, self.company_currency, self.posting_date
				)

	def set_target_exchange_rate(self, ref_doc=None):
		if self.paid_from_account_currency == self.paid_to_account_currency:
			self.target_exchange_rate = self.source_exchange_rate
		elif self.paid_to and not self.target_exchange_rate:
			if ref_doc:
				if self.paid_to_account_currency == ref_doc.currency:
					self.target_exchange_rate = ref_doc.get("exchange_rate") or ref_doc.get("conversion_rate")

			if not self.target_exchange_rate:
				self.target_exchange_rate = get_exchange_rate(
					self.paid_to_account_currency, self.company_currency, self.posting_date
				)


	def set_amounts(self):
		self.set_received_amount()
		self.set_amounts_in_company_currency()
		self.set_total_allocated_amount()
		self.set_unallocated_amount()
		self.set_exchange_gain_loss()
		self.set_difference_amount()


	def set_received_amount(self):
		self.base_received_amount = self.base_paid_amount
		if (
			self.paid_from_account_currency == self.paid_to_account_currency
			and not self.payment_type == "Internal Transfer"
		):
			self.received_amount = self.paid_amount


	def set_amounts_in_company_currency(self):
		self.base_paid_amount, self.base_received_amount, self.difference_amount = 0, 0, 0
		if self.paid_amount:
			self.base_paid_amount = flt(
				flt(self.paid_amount) * flt(self.source_exchange_rate), self.precision("base_paid_amount")
			)

		if self.received_amount:
			self.base_received_amount = flt(
				flt(self.received_amount) * flt(self.target_exchange_rate),
				self.precision("base_received_amount"),
			)

	def calculate_base_allocated_amount_for_reference(self, d) -> float:
		base_allocated_amount = 0
		if d.reference_doctype in frappe.get_hooks("advance_payment_doctypes"):
			# When referencing Sales/Purchase Order, use the source/target exchange rate depending on payment type.
			# This is so there are no Exchange Gain/Loss generated for such doctypes

			exchange_rate = 1
			if self.payment_type == "Receive":
				exchange_rate = self.source_exchange_rate
			elif self.payment_type == "Pay":
				exchange_rate = self.target_exchange_rate

			base_allocated_amount += flt(
				flt(d.allocated_amount) * flt(exchange_rate), self.precision("base_paid_amount")
			)
		else:

			exchange_rate = 1
			if self.payment_type == "Receive":
				exchange_rate = self.source_exchange_rate
			elif self.payment_type == "Pay":
				exchange_rate = self.target_exchange_rate

			base_allocated_amount += flt(
				flt(d.allocated_amount) * flt(exchange_rate), self.precision("base_paid_amount")
			)

			if d.exchange_rate is None:
				d.exchange_rate = 1

			allocated_amount_in_ref_exchange_rate = flt(
				flt(d.allocated_amount) * flt(d.exchange_rate), self.precision("base_paid_amount")
			)
			d.exchange_gain_loss = base_allocated_amount - allocated_amount_in_ref_exchange_rate
		return base_allocated_amount

	def set_total_allocated_amount(self):
		if self.payment_type == "Internal Transfer":
			return

		total_allocated_amount, base_total_allocated_amount = 0, 0
		for d in self.get("references"):
			if d.allocated_amount:
				total_allocated_amount += flt(d.allocated_amount)
				base_total_allocated_amount += self.calculate_base_allocated_amount_for_reference(d)

		self.total_allocated_amount = abs(total_allocated_amount)
		self.base_total_allocated_amount = abs(base_total_allocated_amount)

	def set_unallocated_amount(self):
		self.unallocated_amount = 0
		if not self.party:
			return

		deductions_to_consider = sum(
			flt(d.amount) for d in self.get("deductions") if not d.is_exchange_gain_loss
		)
		included_taxes = self.get_included_taxes()

		if self.payment_type == "Receive" and self.base_total_allocated_amount < (
			self.base_paid_amount + deductions_to_consider
		):
			self.unallocated_amount = (
				self.base_paid_amount
				+ deductions_to_consider
				- self.base_total_allocated_amount
				- included_taxes
			) / self.source_exchange_rate
		elif self.payment_type == "Pay" and self.base_total_allocated_amount < (
			self.base_received_amount - deductions_to_consider
		):
			self.unallocated_amount = (
				self.base_received_amount
				- deductions_to_consider
				- self.base_total_allocated_amount
				- included_taxes
			) / self.target_exchange_rate

	def set_exchange_gain_loss(self):
		exchange_gain_loss = flt(
			self.base_paid_amount - self.base_received_amount,
			self.precision("amount", "deductions"),
		)

		exchange_gain_loss_rows = [row for row in self.get("deductions") if row.is_exchange_gain_loss]
		exchange_gain_loss_row = exchange_gain_loss_rows.pop(0) if exchange_gain_loss_rows else None

		for row in exchange_gain_loss_rows:
			self.remove(row)

		if not exchange_gain_loss:
			if exchange_gain_loss_row:
				self.remove(exchange_gain_loss_row)

			return

		if not exchange_gain_loss_row:
			values = frappe.get_cached_value(
				"Company", self.company, ("exchange_gain_loss_account", "cost_center"), as_dict=True
			)

			for fieldname, value in values.items():
				if value:
					continue

				label = _(frappe.get_meta("Company").get_label(fieldname))
				return frappe.msgprint(
					_("Please set {0} in Company {1} to account for Exchange Gain / Loss").format(
						label, get_link_to_form("Company", self.company)
					),
					title=_("Missing Default in Company"),
					indicator="red" if self.docstatus.is_submitted() else "yellow",
					raise_exception=self.docstatus.is_submitted(),
				)

			exchange_gain_loss_row = self.append(
				"deductions",
				{
					"account": values.exchange_gain_loss_account,
					"cost_center": values.cost_center,
					"is_exchange_gain_loss": 1,
				},
			)

		exchange_gain_loss_row.amount = exchange_gain_loss

	def set_difference_amount(self):
		base_unallocated_amount = flt(self.unallocated_amount) * (
			flt(self.source_exchange_rate)
			if self.payment_type == "Receive"
			else flt(self.target_exchange_rate)
		)

		base_party_amount = flt(self.base_total_allocated_amount) + flt(base_unallocated_amount)
		included_taxes = self.get_included_taxes()

		if self.payment_type == "Receive":
			self.difference_amount = base_party_amount - self.base_received_amount + included_taxes
		elif self.payment_type == "Pay":
			self.difference_amount = self.base_paid_amount - base_party_amount - included_taxes
		else:
			self.difference_amount = self.base_paid_amount - flt(self.base_received_amount) - included_taxes

		total_deductions = sum(flt(d.amount) for d in self.get("deductions"))

		self.difference_amount = flt(
			self.difference_amount - total_deductions, self.precision("difference_amount")
		)

	def get_included_taxes(self):
		included_taxes = 0
		for tax in self.get("taxes"):
			if not tax.included_in_paid_amount:
				continue

			if tax.add_deduct_tax == "Add":
				included_taxes += tax.base_tax_amount
			else:
				included_taxes -= tax.base_tax_amount

		return included_taxes


	def set_gain_or_loss(self, account_details=None):
		if not self.difference_amount:
			self.set_difference_amount()

		row = {"amount": self.difference_amount}

		if account_details:
			row.update(account_details)

		if not row.get("amount"):
			return

		self.append("deductions", row)
		self.set_unallocated_amount()


	@frappe.whitelist()
	def allocate_amount_to_references(self, paid_amount, paid_amount_change, allocate_payment_amount):
		"""
		Allocate `Allocated Amount` and `Payment Request` against `Reference` based on `Paid Amount` and `Outstanding Amount`.\n
		:param paid_amount: Paid Amount / Received Amount.
		:param paid_amount_change: Flag to check if `Paid Amount` is changed or not.
		:param allocate_payment_amount: Flag to allocate amount or not. (Payment Request is also dependent on this flag)
		"""
		if not self.references:
			return

		if not allocate_payment_amount:
			for ref in self.references:
				ref.allocated_amount = 0
			return

		# calculating outstanding amounts
		precision = self.precision("paid_amount")
		total_positive_outstanding_including_order = 0
		total_negative_outstanding = 0
		paid_amount -= sum(flt(d.amount, precision) for d in self.deductions)

		for ref in self.references:
			reference_outstanding_amount = flt(ref.outstanding_amount)
			abs_outstanding_amount = abs(reference_outstanding_amount)

			if reference_outstanding_amount > 0:
				total_positive_outstanding_including_order += abs_outstanding_amount
			else:
				total_negative_outstanding += abs_outstanding_amount

		# calculating allocated outstanding amounts
		allocated_negative_outstanding = 0
		allocated_positive_outstanding = 0

		# checking party type and payment type
		if (self.payment_type == "Receive" and self.party_type == "Customer") or (
			self.payment_type == "Pay" and self.party_type in ("Supplier", "Employee")
		):
			if total_positive_outstanding_including_order > paid_amount:
				remaining_outstanding = flt(
					total_positive_outstanding_including_order - paid_amount, precision
				)
				allocated_negative_outstanding = min(remaining_outstanding, total_negative_outstanding)

			allocated_positive_outstanding = paid_amount + allocated_negative_outstanding

		elif self.party_type in ("Supplier", "Employee"):
			if paid_amount > total_negative_outstanding:
				if total_negative_outstanding == 0:
					frappe.msgprint(
						_("Cannot {0} from {1} without any negative outstanding invoice").format(
							self.payment_type,
							self.party_type,
						)
					)
				else:
					frappe.msgprint(
						_("Paid Amount cannot be greater than total negative outstanding amount {0}").format(
							total_negative_outstanding
						)
					)

				return

			else:
				allocated_positive_outstanding = flt(total_negative_outstanding - paid_amount, precision)
				allocated_negative_outstanding = paid_amount + min(
					total_positive_outstanding_including_order, allocated_positive_outstanding
				)

		# inner function to set `allocated_amount` to those row which have no PR
		def _allocation_to_unset_pr_row(
			row, outstanding_amount, allocated_positive_outstanding, allocated_negative_outstanding
		):
			if outstanding_amount > 0 and allocated_positive_outstanding >= 0:
				row.allocated_amount = min(allocated_positive_outstanding, outstanding_amount)
				allocated_positive_outstanding = flt(
					allocated_positive_outstanding - row.allocated_amount, precision
				)
			elif outstanding_amount < 0 and allocated_negative_outstanding:
				row.allocated_amount = min(allocated_negative_outstanding, abs(outstanding_amount)) * -1
				allocated_negative_outstanding = flt(
					allocated_negative_outstanding - abs(row.allocated_amount), precision
				)
			return allocated_positive_outstanding, allocated_negative_outstanding

		# allocate amount based on `paid_amount` is changed or not
		if not paid_amount_change:
			for ref in self.references:
				allocated_positive_outstanding, allocated_negative_outstanding = _allocation_to_unset_pr_row(
					ref,
					ref.outstanding_amount,
					allocated_positive_outstanding,
					allocated_negative_outstanding,
				)

			allocate_open_payment_requests_to_references(self.references, self.precision("paid_amount"))

		else:
			payment_request_outstanding_amounts = (
				get_payment_request_outstanding_set_in_references(self.references) or {}
			)
			references_outstanding_amounts = get_references_outstanding_amount(self.references) or {}
			remaining_references_allocated_amounts = references_outstanding_amounts.copy()

			# Re allocate amount to those references which have PR set (Higher priority)
			for ref in self.references:
				if not ref.payment_request:
					continue

				# fetch outstanding_amount of `Reference` (Payment Term) and `Payment Request` to allocate new amount
				key = (ref.reference_doctype, ref.reference_name, ref.get("payment_term"))
				reference_outstanding_amount = references_outstanding_amounts[key]
				pr_outstanding_amount = payment_request_outstanding_amounts[ref.payment_request]

				if reference_outstanding_amount > 0 and allocated_positive_outstanding >= 0:
					# allocate amount according to outstanding amounts
					outstanding_amounts = (
						allocated_positive_outstanding,
						reference_outstanding_amount,
						pr_outstanding_amount,
					)

					ref.allocated_amount = min(outstanding_amounts)

					# update amounts to track allocation
					allocated_amount = ref.allocated_amount
					allocated_positive_outstanding = flt(
						allocated_positive_outstanding - allocated_amount, precision
					)
					remaining_references_allocated_amounts[key] = flt(
						remaining_references_allocated_amounts[key] - allocated_amount, precision
					)
					payment_request_outstanding_amounts[ref.payment_request] = flt(
						payment_request_outstanding_amounts[ref.payment_request] - allocated_amount, precision
					)

				elif reference_outstanding_amount < 0 and allocated_negative_outstanding:
					# allocate amount according to outstanding amounts
					outstanding_amounts = (
						allocated_negative_outstanding,
						abs(reference_outstanding_amount),
						pr_outstanding_amount,
					)

					ref.allocated_amount = min(outstanding_amounts) * -1

					# update amounts to track allocation
					allocated_amount = abs(ref.allocated_amount)
					allocated_negative_outstanding = flt(
						allocated_negative_outstanding - allocated_amount, precision
					)
					remaining_references_allocated_amounts[key] += allocated_amount  # negative amount
					payment_request_outstanding_amounts[ref.payment_request] = flt(
						payment_request_outstanding_amounts[ref.payment_request] - allocated_amount, precision
					)
			# Re allocate amount to those references which have no PR (Lower priority)
			for ref in self.references:
				if ref.payment_request:
					continue

				key = (ref.reference_doctype, ref.reference_name, ref.get("payment_term"))
				reference_outstanding_amount = remaining_references_allocated_amounts[key]

				allocated_positive_outstanding, allocated_negative_outstanding = _allocation_to_unset_pr_row(
					ref,
					reference_outstanding_amount,
					allocated_positive_outstanding,
					allocated_negative_outstanding,
				)


def add_tax_discount_loss(pe, doc, total_discount_percentage) -> float:
	"""Add loss on tax discount in base currency."""
	tax_discount_loss = {}
	base_total_tax_loss = 0
	precision = doc.precision("tax_amount_after_discount_amount", "taxes")

	# The same account head could be used more than once
	for tax in doc.get("taxes", []):
		base_tax_loss = tax.get("base_tax_amount_after_discount_amount") * (total_discount_percentage / 100)

		account = tax.get("account_head")
		if not tax_discount_loss.get(account):
			tax_discount_loss[account] = base_tax_loss
		else:
			tax_discount_loss[account] += base_tax_loss

	for account, loss in tax_discount_loss.items():
		base_total_tax_loss += loss
		if loss == 0.0:
			continue

		pe.append(
			"deductions",
			{
				"account": account,
				"cost_center": pe.cost_center
				or frappe.get_cached_value("Company", pe.company, "cost_center"),
				"amount": flt(loss, precision),
			},
		)

	return base_total_tax_loss  # Return loss without rounding


