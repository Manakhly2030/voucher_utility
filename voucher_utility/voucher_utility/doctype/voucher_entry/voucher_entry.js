// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Voucher Entry', {
    mode_of_payment: function(frm) {
        var mode_of_payment = frm.doc.mode_of_payment;
        frappe.call({
            method: 'frappe.client.get',
            args: {
                'doctype': 'Mode of Payment',
                'filters': {'name': mode_of_payment},
                'fieldname': ['accounts']
            },
            callback: function(response) {
                if (response && response.message && response.message.accounts && response.message.accounts.length > 0) {
                    var defaultAccount = response.message.accounts[0].default_account;
                    frm.set_value('account', defaultAccount);
                }
            }
        });
    },
    setup(frm){
        frm.set_query('account', 'voucher_accounts', function(doc, cdt, cdn) {
            return {
                filters: {
                    is_group: 0
                }
            }
        });
        frm.set_query('party_type', 'voucher_accounts', function(doc, cdt, cdn) {
            const row = locals[cdt][cdn];
            return {
                query: 'erpnext.setup.doctype.party_type.party_type.get_party_type',
                filters: {
                    account: row.account
                }
            };
        });


    },
  refresh: function(frm) {
        // Automatically fetch the balance when an account is selected
        if (frm.doc.docstatus === 1) {
         frm.add_custom_button(__('View'), function(){
           frappe.call({
           method: "voucher_utility.voucher_utility.doctype.voucher_entry.voucher_entry.view_journal_entry",
           args: {
             'voucher_entry':frm.doc.name
           },
           callback: function(r) {
             if (r.message){
               frappe.set_route('Form','Journal Entry', r.message);
               }
             }
           });
        });
     }
   },
   account: function(frm){
     if (frm.doc.account) {
         frappe.call({
             method: 'erpnext.accounts.utils.get_balance_on',
             args: {
                 account: frm.doc.account,
             },
             callback: function(r) {
                 if (r.message) {
                     frm.set_value('balance', r.message); // Set the balance field in the form
                 }
             }
         });
     }
   }

  });

frappe.ui.form.on('Voucher Account', {
    voucher_account_add: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    },
    voucher_account_remove: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    },
    amount: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    },
    voucher_entry_type: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.voucher_entry_type) {
          if (!frm.doc.company) {
              frappe.model.set_value(cdt, cdn, 'voucher_entry_type', );
              frappe.msgprint(__('Please set the company'));
              return;
          }
          // Validate if the company is associated with the selected voucher entry type
            frappe.call({
                method: 'voucher_utility.voucher_utility.doctype.voucher_entry.voucher_entry.validate_company_for_voucher_entry_type',
                args: {
                    voucher_entry_type: row.voucher_entry_type,
                    company: frm.doc.company
                },
                callback: function(response) {
                    if (!response.message) {
                    }
                },
                error: function(err) {
                }
            });
            // Fetch and set the default account after validation
            frappe.call({
                method: 'voucher_utility.voucher_utility.doctype.voucher_entry.voucher_entry.get_default_account',
                args: {
                    voucher_entry_type: row.voucher_entry_type,
                    company: frm.doc.company
                },
                callback: function(response) {
                    if (response.message) {
                        let default_account = response.message;
                        frappe.model.set_value(cdt, cdn, 'account', default_account);
                    }
                }
            });
        }
    }
});

function calculate_total_amount(frm) {
    let total = 0;
    frm.doc.voucher_accounts.forEach(function(row) {
        if (row.amount) {
            total += row.amount;
        }
    });
    frm.set_value('total_amount', total);
}
