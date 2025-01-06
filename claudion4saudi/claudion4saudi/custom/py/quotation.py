import frappe


@frappe.whitelist()
def sales_invoice_list(item, company):
    if item and company:
        # Query to fetch Sales Invoice items
        si_list = frappe.db.sql("""
            SELECT 
                sii.parent, 
                sii.rate ,
                si.party_name
            FROM 
                `tabQuotation Item` sii
            JOIN 
                `tabQuotation` si ON si.name = sii.parent
            WHERE 
                sii.item_code = %s
                AND si.company = %s
                AND si.quotation_to = "Customer"
                AND si.docstatus = 1   -- Ensure the invoice is submitted (docstatus = 1)
            ORDER BY 
                sii.parent DESC  -- Sort by parent in descending order
            LIMIT 5  -- Limit to 5 rows
        """, (item, company), as_dict=True)

        # Query to fetch Purchase Invoice items
        pi_list = frappe.db.sql("""
            SELECT 
                pii.parent, 
                pii.rate,
                pi.supplier
            FROM 
                `tabPurchase Invoice Item` pii
            JOIN 
                `tabPurchase Invoice` pi ON pi.name = pii.parent
            WHERE 
                pii.item_code = %s
                AND pi.company = %s
                AND pi.is_return = 0  -- Ensure it's not a return invoice
                AND pi.docstatus = 1   -- Ensure the invoice is submitted (docstatus = 1)
            ORDER BY 
                pii.parent DESC  -- Sort by parent in descending order
            LIMIT 5  -- Limit to 5 rows
        """, (item, company), as_dict=True)
        
        return {"si_list": si_list, "pi_list": pi_list}
    

@frappe.whitelist()
def fetch_rate_details(item_code, customer):
    doc_count = 0
    rate_details = []

    so_details = frappe.get_all(
        'Quotation Item',
        ['rate', 'parent'],
        {
            'item_code': item_code,
            'parenttype': 'Quotation',
            'docstatus': 1
        },
        order_by="modified"
    )

    for row in so_details[::-1]:
        if frappe.db.get_value('Quotation', row.parent, 'docstatus') == 1:
            so_doc = frappe.get_doc('Quotation', row.parent)

            # Check if the customer matches the specified customer
            if so_doc.party_name == customer:
                rate_details.append(
                    {
                        'quotation': row.parent,
                        'date': so_doc.transaction_date,
                        'customer': so_doc.party_name, 
                        'rate': row.rate
                    }
                )
                doc_count += 1
            if doc_count == 5:
                break

    return rate_details