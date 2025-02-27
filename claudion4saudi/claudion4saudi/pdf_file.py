import frappe
import pdfplumber
import re
import json
from pdf2image import convert_from_path
import pytesseract
import fitz
from frappe.utils.file_manager import save_file

from pdf2image import convert_from_bytes
from io import BytesIO
# Initialize Frappe
# frappe.init(site="zatca-live.erpgulf.com")
# frappe.connect()
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

@frappe.whitelist(allow_guest=True)
def pdf_to_json():
    try:
        uploaded_file = frappe.request.files.get("file")
        company_name = frappe.form_dict.get("company_name")

        if not uploaded_file:
            return {"error": "Missing required parameter: 'file'"}
        if not company_name:
            return {"error": "Missing required parameter: 'company_name'"}

        pdf_bytes = uploaded_file.read()
        extracted_text = extract_text_from_pdf_bytes(pdf_bytes)

        if not extracted_text.strip():
            return {"error": "Failed to extract text from the provided PDF."}

        pdf_mapping = get_company_pdf_mapping(company_name)

        if not pdf_mapping:
            return {"error": f"No PDF Mapping JSON found for company: {company_name}"}

        invoice_data = extract_invoice_details_from_text(extracted_text, pdf_mapping, company_name)

        save_json(invoice_data)

        return {"invoice_data": invoice_data}

    except Exception as e:
        frappe.log_error(f"Error processing PDF: {str(e)}")
        return {"error": "Internal Server Error", "details": str(e)}


def get_company_pdf_mapping(company_name):
    file_doc = frappe.get_all(
        "File",
        filters={"attached_to_doctype": "Company", "attached_to_name": company_name.strip()},
        fields=["file_url"]
    )

    if not file_doc:
        frappe.msgprint(f"No PDF Mapping JSON found in Company attachments for {company_name}.")
        return None

    json_file_url = file_doc[0]["file_url"]
    json_file_path = frappe.get_site_path(json_file_url.strip("/"))

    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            pdf_mapping = json.load(f)
        return pdf_mapping
    except Exception as e:
        frappe.msgprint(f"Error Loading JSON Template: {e}")
        return None


def extract_text_from_pdf_bytes(pdf_bytes):
    extracted_text = ""
    pdf_file = BytesIO(pdf_bytes)

    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"

        if extracted_text.strip():
            return extracted_text
    except Exception as e:
        frappe.msgprint(f"Error using pdfplumber: {e}")

    try:
        images = convert_from_bytes(pdf_bytes, dpi=300)
        for image in images:
            extracted_text += pytesseract.image_to_string(image) + "\n"
    except Exception as e:
        frappe.msgprint(f"OCR extraction failed: {e}")

    return extracted_text


def extract_address_details(text, start_keyword, end_keywords):
    pattern = rf"{start_keyword}([\s\S]*?)(?={'|'.join(end_keywords)})"
    match = re.search(pattern, text, re.MULTILINE)

    if match:
        full_address = match.group(1).strip().split("\n")
        full_address = [
            line.strip() for line in full_address 
            if line.strip() and not re.search(r"Page\s*\d+|Date\s*\d{2}/\d{2}/\d{4}", line, re.IGNORECASE)
        ]

        city = full_address[-2] if len(full_address) >= 2 else "Not Found"
        country = full_address[-1] if len(full_address) >= 1 else "Not Found"

        clean_address = " ".join(full_address)

        return clean_address, city, country

    return "Not Found", "Not Found", "Not Found"


def extract_invoice_details_from_text(extracted_text, pdf_mapping,company_name):
    invoice_details = {}

    for key, pattern in pdf_mapping.items():
        if isinstance(pattern, dict):
            invoice_details[key] = {}
            for sub_key, sub_pattern in pattern.items():
                if isinstance(sub_pattern, str) or isinstance(sub_pattern, list):
                    invoice_details[key][sub_key] = find_match(sub_pattern, extracted_text)

            if key == "supplier":
                supplier_address, supplier_city, supplier_country = extract_address_details(
                    extracted_text, company_name, ["TIN NO"]
                )
                invoice_details[key]["address"] = supplier_address
                invoice_details[key]["city"] = supplier_city
                invoice_details[key]["country"] = supplier_country

            if key == "customer":
                customer_address, customer_city, customer_country = extract_address_details(
                    extracted_text, "Customer Address:", ["Customer Email", "Customer Tel No"]
                )
                invoice_details[key]["address"] = customer_address
                invoice_details[key]["city"] = customer_city
                invoice_details[key]["country"] = customer_country
        
        elif isinstance(pattern, list):
            invoice_details[key] = find_match(pattern, extracted_text)
        
        elif isinstance(pattern, str):
            invoice_details[key] = find_match(pattern, extracted_text)

    invoice_details["line_items"] = extract_line_items(extracted_text, pdf_mapping)
    return invoice_details


def find_match(patterns, text):
    if isinstance(patterns, str):
        patterns = [patterns]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip() if match.lastindex else match.group(0).strip()
    
    return "Not Found"


def extract_line_items(extracted_text, pdf_mapping):
    line_items = []
    line_item_config = pdf_mapping.get("line_items", {})

    if not isinstance(line_item_config, dict):
        frappe.msgprint("Error: 'line_items' format in template is incorrect. Expected a dictionary.")
        return []

    line_pattern = line_item_config.get("pattern", "")

    if not line_pattern:
        frappe.msgprint(" No line items pattern found in the template.")
        return []

    matches = re.findall(line_pattern, extracted_text, re.MULTILINE)

    def safe_float(value):
        value = re.sub(r"[^\d.]", "", value.replace(",", ""))
        return float(value) if value else 0.0

    fields = line_item_config.get("fields", [])

    for match in matches:
        item = {}
        for i, field in enumerate(fields):
            if i < len(match):
                item[field] = safe_float(match[i]) if "Price" in field or "Quantity" in field else match[i].strip()
        line_items.append(item)

    return line_items


def save_json(invoice_data):
    output_json_path = "/opt/Claudion4Saudi/frappe-bench/apps/claudion4saudi/claudion4saudi/claudion4saudi/result.json"
    try:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(invoice_data, f, indent=4)
        frappe.msgprint(f"\n Invoice data saved to {output_json_path}")
    except Exception as e:
        frappe.msgprint(f"Error saving JSON: {e}")
















# @frappe.whitelist(allow_guest=True)
# def create_invoices_from_json():
#     if not hasattr(frappe.local, "flags"):
#         frappe.local.flags = frappe._dict()

#     uploaded_file = frappe.request.files.get("file")  
#     if not uploaded_file:
#         return {"error": "Missing required parameter: 'file'"}

#     pdf_bytes = uploaded_file.read()

#     invoice_id = frappe.form_dict.get("invoice_id") 
#     zimra_submit = frappe.form_dict.get("zimra_submit", False) 
#     json_path = "/opt/Claudion4Saudi/frappe-bench/apps/claudion4saudi/claudion4saudi/claudion4saudi/result.json"

#     try:
#         with open(json_path, "r") as f:
#             invoice_data = json.load(f)
#     except FileNotFoundError:
#         return {"error": "Invoice JSON file not found."}, 404  
    
#     if not hasattr(frappe.local, "flags"):
#         frappe.local.flags = frappe._dict()


#     if invoice_id and zimra_submit:
#         if not frappe.db.exists("Sales Invoice", invoice_id):
#             return {"error": f"Invoice ID {invoice_id} not found"}, 404

#         invoice = frappe.get_doc("Sales Invoice", invoice_id)
#         qr_code_string = invoice.get("custom_qr_string_data", "")
#         zimra_response = invoice.get("custom_zimra_response", "")

#         updated_pdf_path = write_qr_code_to_pdf(pdf_bytes, qr_code_string, zimra_response)

#         with open(updated_pdf_path, "rb") as f:
#             file_content = f.read()

#         file_doc = save_file(
#             fname=updated_pdf_path.split("/")[-1], 
#             content=file_content,
#             dt="Sales Invoice", 
#             dn=str(invoice_id), 
#             folder="Home/Attachments",
#             is_private=0
#         )

#         return json.dumps({
#             "message": f"Invoice details for {invoice_id} with QR Code & ZIMRA Response written to PDF",
#             "invoice_id": invoice.name,
#             "attached_pdf": file_doc.file_url  
#         })
    
#     invoices_created = []
#     customer_name = invoice_data.get("customer")
#     customer_address = invoice_data.get("customer_address", "").replace("\n", " ")

#     if not frappe.db.exists("Customer", customer_name):
#         new_customer = frappe.get_doc({
#             "doctype": "Customer",
#             "customer_name": customer_name,
#             "customer_type": "Company",
#             "customer_group": "All Customer Groups",
#             "territory": "All Territories",
#             "customer_primary_contact": invoice_data.get("email", ""),
#             "tax_id": invoice_data.get("customer_tin", ""),
#         })
#         new_customer.insert(ignore_permissions=True, ignore_links=True)
#         frappe.db.commit()
#         frappe.msgprint(f"New Customer '{customer_name}' created.", alert=True)

#     # if not frappe.db.exists("Address", {"customer": customer_name}):
#     #     new_customer_address = frappe.get_doc({
#     #         "doctype": "Address",
#     #         "address_title": customer_name,
#     #         "address_type": "Billing",
#     #         "address_line1": customer_address,
#     #         "city": invoice_data.get("customer_city", ""),
#     #         "state": invoice_data.get("customer_state", ""),cc
#     #         "country": invoice_data.get("customer_country", ""),
#     #         "pincode": 45676,
#     #         "email_id":invoice_data.get("email"),
#     #         # "phone":invoice_data.get(phone),
#     #         "links": [{"link_doctype": "Customer", "link_name": customer_name}]
#     #     })
#     #     new_customer_address.insert(ignore_permissions=True, ignore_links=True)
#     #     frappe.db.commit()
#     #     frappe.msgprint(f"New Address for '{customer_name}' created.", alert=True)

#     supplier_name = invoice_data.get("supplier")
#     supplier_address = invoice_data.get("supplier_address", "").replace("\n", " ")

#     if not frappe.db.exists("Company", supplier_name):
#         new_company = frappe.get_doc({
#             "doctype": "Company",
#             "company_name": supplier_name,
#             "default_currency": "USD",
#         })
#         new_company.insert(ignore_permissions=True, ignore_links=True)
#         frappe.db.commit()
#         frappe.msgprint(f"New Company '{supplier_name}' created.", alert=True)






#     invoice_doc = {
#         "doctype": "Sales Invoice",
#         "customer": customer_name,
#         "posting_date": frappe.utils.today(),
#         "due_date": frappe.utils.add_days(frappe.utils.today(), 7),
#         "company": supplier_name,
#         "currency": "USD",
#         "exchange_rate": 1.0,  
#         "items": [],
#         "taxes": [],
#         "total": invoice_data.get("total"),
#     }

#     for item in invoice_data.get("line_items", []):
#         item_code = item.get("Code", "")
#         item_name = item.get("Description", "")

#         if not frappe.db.exists("Item", item_code):
#             new_item = frappe.get_doc({
#                 "doctype": "Item",
#                 "item_code": item_code,
#                 "item_name": item_name,
#                 "item_group": "All Item Groups",
#                 "stock_uom": "Nos",
#                 "is_sales_item": 1,
#                 "standard_rate": float(item.get("Unit Price (Incl.)", "0") or "0"),
#                 "taxes": [{"item_tax_template": "Zimbabwe Tax - HT"}], 
#             })
#             new_item.insert(ignore_permissions=True, ignore_links=True)
#             frappe.db.commit()

#         Unit_Price = float(item.get("Unit Price (Incl.)", "0").replace("USD", "").strip())  
#         VAT_Amount = float(item.get("VAT Amount", "0").replace("USD", "").strip())  
#         rate = Unit_Price - VAT_Amount

#         invoice_doc["items"].append({
#             "item_code": item_code,
#             "item_name": item_name,
#             "qty": float(item.get("Quantity")),
#             "rate": rate,
#             "item_tax_template": "Zimbabwe Tax - HT",
#         })
#     vat_total = float(invoice_data.get("vat_total"))
#     subtotal = float(invoice_data.get("subtotal"))
#     tax_rate = round((vat_total * 100 / subtotal), 2) if subtotal else 0

#     invoice_doc["taxes"].append({
#         "charge_type": "On Net Total",
#         "account_head": "Freight and Forwarding Charges - HT",
#         "description": "this is ",
#         "rate": tax_rate,
#     })


#     new_invoice = frappe.get_doc(invoice_doc)
#     new_invoice.insert(ignore_permissions=True, ignore_links=True)
#     new_invoice.save()

#     invoices_created.append(new_invoice.name)

#     return json.dumps({"message": f"{len(invoices_created)} invoice(s) created.", "invoices": invoices_created})




# def write_qr_code_to_pdf(pdf_bytes, qr_code_string, zimra_response):
#     doc = fitz.open(stream=pdf_bytes, filetype="pdf")

#     new_page = doc.new_page(width=595, height=842)

#     new_page.insert_text((50, 100), "QR Code Data:", fontsize=12, color=(0, 0, 0))
#     new_page.insert_text((50, 120), qr_code_string, fontsize=10, color=(0, 0, 0))

#     response_lines = zimra_response.split()
#     formatted_lines = "\n".join([" ".join(response_lines[i:i+10]) for i in range(0, len(response_lines), 10)])

#     new_page.insert_text((50, 160), "ZIMRA Response:", fontsize=12, color=(0, 0, 0))
#     new_page.insert_textbox((50, 180, 500, 400), formatted_lines, fontsize=10, color=(0, 0, 0))

#     output_pdf_path = "/tmp/Updated_Invoice.pdf"
#     doc.save(output_pdf_path)
#     doc.close()

#     return output_pdf_path