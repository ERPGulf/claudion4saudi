import frappe
import csv
from io import StringIO
from datetime import datetime
from collections import defaultdict

@frappe.whitelist(allow_guest=True)
def create_pos_invoices():
    def set_404_response(message):
        frappe.local.response.update({"http_status_code": 404, "message": message})
    
    if frappe.request.method != "POST":
        return set_404_response("Only POST requests are allowed.")
    
    uploaded_file = frappe.request.files.get("file")
    image_files = frappe.request.files.getlist("images")

    if not uploaded_file:
        return set_404_response("No CSV file uploaded.")
    if not uploaded_file.filename.endswith('.csv'):
        return set_404_response("Uploaded file must be a CSV.")
    if not image_files:
        return set_404_response("No image files uploaded.")

    file_content = uploaded_file.read().decode("utf-8")
    csv_data = list(csv.DictReader(StringIO(file_content)))

    image_map = {img.filename: img for img in image_files}

    invoices_data = defaultdict(lambda: {"items": [], "details": {}})
    invoices_created = []
    current_invoice_id = None

    for row_num, row in enumerate(csv_data, start=1):
        customer = row.get("Customer")
        invoice_id = row.get("ID")

        if invoice_id:
            invoices_data[invoice_id]["details"] = {
                "customer": customer,
                "company": row.get("Company"),
                "posting_date": row.get("Date"),
                "currency": row.get("Currency", "USD"),
                "exchange_rate": row.get("Exchange Rate", "1"),
                "due_date": datetime.strptime(
                    row.get("Due Date (Payment Schedule)", datetime.today().strftime("%m/%d/%Y")),
                    "%m/%d/%Y"
                ).strftime("%Y-%m-%d"),
                "attachment": row.get("Attachments")  
            }
            
            item = {
                "item_code": row.get("Item Name (Items)"),
                "qty": float(row.get("UOM Conversion Factor (Items)", "1")),
                "rate": float(row.get("Rate (Items)", "0")),
                "uom": row.get("UOM (Items)", "Nos"),
                "cost_center": row.get("Cost Center (Items)"),
                "income_account": row.get("Income Account (Items)"),
                "amount": float(row.get("Amount (Items)", "0")),
            }
            invoices_data[invoice_id]["items"].append(item)
            current_invoice_id = invoice_id
        else:
            if current_invoice_id:
                item = {
                    "item_code": row.get("Item Name (Items)"),
                    "qty": float(row.get("UOM Conversion Factor (Items)", "1")),
                    "rate": float(row.get("Rate (Items)", "0")),
                    "uom": row.get("UOM (Items)", "Nos"),
                    "cost_center": row.get("Cost Center (Items)"),
                    "income_account": row.get("Income Account (Items)"),
                    "amount": float(row.get("Amount (Items)", "0")),
                }
                invoices_data[current_invoice_id]["items"].append(item)
            else:
                 return {"message": f"Skipping row {row_num} due to missing Invoice ID."}

    for invoice_id, data in invoices_data.items():
        details = data["details"]

        default_mode_of_payment = "Cash"
        total_amount = sum(item.get("amount", 0) for item in data["items"])

        new_invoice = frappe.get_doc({
            "doctype": "POS Invoice",
            "customer": details["customer"],
            "company": details["company"],
            "posting_date": details["posting_date"],
            "currency": details["currency"],
            "exchange_rate": details["exchange_rate"],
            "due_date": details["due_date"],
            "items": data["items"],
            "payments": [
                {
                    "mode_of_payment": default_mode_of_payment,
                    "amount": total_amount,
                }
            ],
        })

        new_invoice.insert(ignore_permissions=True)
        new_invoice.submit()
        invoices_created.append(new_invoice.name)

        attachment_file_name = details.get("attachment")
        if attachment_file_name and attachment_file_name in image_map:
            image_content = image_map[attachment_file_name].read()
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": attachment_file_name,
                "attached_to_doctype": "POS Invoice",
                "attached_to_name": new_invoice.name,
                "content": image_content,
            })
            file_doc.save(ignore_permissions=True)

    return {
        "message": f"{len(invoices_created)} POS Invoices created successfully and Attachment added to POS Invoices",
        "invoices": invoices_created
    }
