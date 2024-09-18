from frappe.model.document import Document
import frappe
from frappe.utils import get_link_to_form
from frappe import _ 

class VoucherEntry(Document):
    def on_submit(self):
        self.create_journal_entry()

    def create_journal_entry(self):
        mode_of_payment = self.mode_of_payment
        if mode_of_payment:
            mode_of_payment_doc = frappe.get_doc('Mode of Payment', self.mode_of_payment)
            for df_account in mode_of_payment_doc.accounts:
                default_account = df_account.default_account
        if not default_account:
            frappe.throw(f"Default account not defined for mode of payment: {mode_of_payment}")

        journal_entry = frappe.new_doc("Journal Entry")
        journal_entry.posting_date = self.posting_date
        journal_entry.user_remark = self.user_remarks
        journal_entry.cheque_date = self.reference_date
        journal_entry.cheque_no = self.bank_reference
        journal_entry.voucher_type = "Journal Entry"

        if self.payment_type == 'Pay':
            journal_entry.append('accounts', {
                'account': default_account,
                'credit_in_account_currency': self.total_amount
            })
            for voucher_account in self.voucher_accounts:
                journal_entry.append('accounts', {
                    'account': voucher_account.account,
                    'party_type': voucher_account.party_type,
                    'party': voucher_account.party,
                    'reference_type': voucher_account.reference_doctype,
                    'reference_name': voucher_account.reference_docname,
                    'debit_in_account_currency': voucher_account.amount
                })

        elif self.payment_type == 'Receive':
            journal_entry.append('accounts', {
                'account': default_account,
                'debit_in_account_currency': self.total_amount
            })
            for voucher_account in self.voucher_accounts:
                journal_entry.append('accounts', {
                    'account': voucher_account.account,
                    'party_type': voucher_account.party_type,
                    'party': voucher_account.party,
                    'reference_type': voucher_account.reference_doctype,
                    'reference_name': voucher_account.reference_docname,
                    'credit_in_account_currency': voucher_account.amount
                })
        journal_entry.reference_voucher_entry = self.name
        journal_entry.submit()
        frappe.msgprint(f"Journal Entry {journal_entry.name} Created successfully.", alert=True, indicator="green")

@frappe.whitelist()
def view_journal_entry(voucher_entry):
    if frappe.db.exists('Journal Entry', {'reference_voucher_entry':voucher_entry}):
        journal_entry = frappe.db.get_value('Journal Entry', {'reference_voucher_entry':voucher_entry})
        return journal_entry


@frappe.whitelist()
def get_default_account(voucher_entry_type, company):
    """
    Retrieve the default account for a given Voucher Entry Type and company.
    Args:
        voucher_entry_type (str): Name of the Voucher Entry Type.
        company (str): Name of the company.
    Returns:
        str: The default account associated with the Voucher Entry Type and company.
    """
    default_account = frappe.db.get_value('Accounts',{'parent': voucher_entry_type, 'parenttype': 'Voucher Entry Type', 'company': company}, 'default_account')
    return default_account

@frappe.whitelist()
def validate_company_for_voucher_entry_type(voucher_entry_type, company):
    """
    Validate if the specified company is associated with the given Voucher Entry Type.
    If the company is not valid, raise a validation error.
    Args:
        voucher_entry_type (str): Name of the Voucher Entry Type.
        company (str): Name of the company.
    Raises:
        frappe.ValidationError: If the company is not associated with the Voucher Entry Type.
    Returns:
        bool: True if the company is valid for the Voucher Entry Type.
    """
    entry_type = frappe.get_doc('Voucher Entry Type', voucher_entry_type)
    valid_companies = [account.company for account in entry_type.accounts]
    if company not in valid_companies:
        frappe.throw(
            _("Set the default account for the {0} {1}").format(
                frappe.bold("Voucher Entry Type\t"),
                get_link_to_form("Voucher Entry Type", voucher_entry_type)
            )
        )
    return True
