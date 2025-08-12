import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from num2words import num2words
from datetime import datetime
import database_manager as db

# --- FONT REGISTRATION (No Changes) ---
FONT_NAME = "DejaVuSans"
FONT_NAME_BOLD = "DejaVuSans-Bold"
try:
    pdfmetrics.registerFont(TTFont(FONT_NAME, "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, "DejaVuSans.ttf"))
    pdfmetrics.registerFontFamily(FONT_NAME, normal=FONT_NAME, bold=FONT_NAME_BOLD, italic=FONT_NAME, boldItalic=FONT_NAME_BOLD)
except Exception as e:
    print(f"--- FONT WARNING ---\nCould not register DejaVuSans.ttf: {e}\nFalling back to Helvetica.")
    FONT_NAME, FONT_NAME_BOLD = "Helvetica", "Helvetica-Bold"

WIDTH, HEIGHT = A4

def create_invoice_pdf(invoice_details, items, settings):
    # This function remains the same
    company_info = settings['company_info']
    bank_details = settings['bank_details']
    invoice_settings = settings['invoice_settings']
    filename = os.path.join("invoices", f"{invoice_details['invoice_no'].replace('/', '_')}.pdf")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    c = canvas.Canvas(filename, pagesize=A4)
    for copy_type in ["Original for Recipient", "Duplicate for Transporter", "Triplicate for Supplier"]:
        draw_invoice_page(c, invoice_details, items, company_info, bank_details, invoice_settings, copy_type)
        c.showPage()
    c.save()
    print(f"Invoice saved: {filename}")
    return filename

def draw_invoice_page(c, invoice_details, items, company_info, bank_details, invoice_settings, copy_type):
    # --- Page Header and Buyer Info (No changes) ---
    c.setFont(FONT_NAME, 8)
    c.drawCentredString(WIDTH / 2, HEIGHT - 15 * mm, copy_type)
    c.setFont(FONT_NAME_BOLD, 16)
    c.drawString(20 * mm, HEIGHT - 25 * mm, company_info['name'])
    c.setFont(FONT_NAME, 9)
    c.drawString(20 * mm, HEIGHT - 31 * mm, company_info['address_line1'])
    c.drawString(20 * mm, HEIGHT - 35 * mm, company_info['address_line2'])
    c.drawString(20 * mm, HEIGHT - 41 * mm, f"GSTIN: {company_info['gstin']} | PAN: {company_info['pan']}")
    c.setFont(FONT_NAME_BOLD, 14)
    c.drawRightString(WIDTH - 20 * mm, HEIGHT - 25 * mm, "TAX INVOICE")
    c.line(20 * mm, HEIGHT - 48 * mm, WIDTH - 20 * mm, HEIGHT - 48 * mm)

    # --- Buyer Details & Invoice Details Tables ---
    y_pos = HEIGHT - 55 * mm
    buyer_details_data = [
        [Paragraph('<b>Bill To:</b>', getSampleStyleSheet()['Normal'])],
        [invoice_details['buyer_name']],
        [invoice_details['buyer_address']],
        [f"GSTIN: {invoice_details['buyer_gstin']}"],
        [f"State: {invoice_details['buyer_state']}"]
    ]
    buyer_table = Table(buyer_details_data, colWidths=[90*mm])
    buyer_table.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), FONT_NAME), ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 1)]))
    buyer_table.wrapOn(c, WIDTH, HEIGHT)
    buyer_table.drawOn(c, 20*mm, y_pos - buyer_table._height)

    invoice_info_data = [
        ['Invoice No:', invoice_details['invoice_no']],
        ['Date:', invoice_details['invoice_date']],
        ['Order Ref:', invoice_details.get('order_ref', 'N/A')],
        ['Dispatch Info:', invoice_details.get('dispatch_info', 'N/A')],
        ['Payment Mode:', invoice_details.get('payment_mode', 'N/A')]
    ]
    invoice_info_table = Table(invoice_info_data, colWidths=[30*mm, 50*mm])
    invoice_info_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('FONTNAME', (0,0), (-1,-1), FONT_NAME), ('ALIGN', (0,0), (0,-1), 'LEFT'), ('ALIGN', (1,0), (1,-1), 'RIGHT')]))
    invoice_info_table.wrapOn(c, WIDTH, HEIGHT)
    invoice_info_table.drawOn(c, WIDTH - 20*mm - 80*mm, y_pos - invoice_info_table._height)
    y_pos -= (invoice_info_table._height + 10 * mm)

    # --- Items Table (No Changes) ---
    items_table_data = [["S.No.", "Description", "HSN", "GST%", "Qty", "Rate", "Disc%", "Amount"]]
    for i, item in enumerate(items, 1):
        items_table_data.append([i, item['description'], item['hsn'], f"{item['gst_rate']:.2f}", f"{item['quantity']}", f"{item['rate']:.2f}", f"{item['discount_percent']:.2f}", f"{item['amount']:.2f}"])
    items_table = Table(items_table_data, colWidths=[12*mm, 68*mm, 15*mm, 10*mm, 15*mm, 20*mm, 10*mm, 20*mm])
    items_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.black), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('ALIGN', (1, 1), (1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD), ('FONTNAME', (0, 1), (-1, -1), FONT_NAME), ('BOTTOMPADDING', (0, 0), (-1, 0), 6), ('TOPPADDING', (0, 1), (-1, -1), 4), ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
    items_table.wrapOn(c, WIDTH, HEIGHT)
    items_table.drawOn(c, 20 * mm, y_pos - items_table._height)
    y_pos -= (items_table._height + 2 * mm)

    # --- Totals Table (Right Side) ---
    taxable_amount = invoice_details['subtotal'] - invoice_details['total_discount']
    totals_data = [['Subtotal', f"₹ {invoice_details['subtotal']:.2f}"], ['Discount', f"- ₹ {invoice_details['total_discount']:.2f}"], ['Taxable Value', f"₹ {taxable_amount:.2f}"]]
    if invoice_details['total_cgst'] > 0: totals_data.extend([['CGST', f"₹ {invoice_details['total_cgst']:.2f}"], ['SGST', f"₹ {invoice_details['total_sgst']:.2f}"]])
    if invoice_details['total_igst'] > 0: totals_data.append(['IGST', f"₹ {invoice_details['total_igst']:.2f}"])
    totals_data.extend([['Freight Charges', f"₹ {invoice_details['freight']:.2f}"], ['Round Off', f"₹ {invoice_details['round_off']:.2f}"], ['GRAND TOTAL', f"₹ {invoice_details['grand_total']:.2f}"]])
    grand_total_row_index = len(totals_data) - 1
    totals_table = Table(totals_data, colWidths=[45*mm, 25*mm])
    totals_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'RIGHT'), ('FONTNAME', (0, 0), (-1, -1), FONT_NAME), ('GRID', (0, 0), (-1, -1), 1, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1, -1), 5), ('RIGHTPADDING', (0,0), (-1, -1), 5), ('BOTTOMPADDING', (0,0), (-1, -1), 3), ('TOPPADDING', (0,0), (-1, -1), 3), ('FONTNAME', (0, 2), (-1, 2), FONT_NAME_BOLD), ('FONTNAME', (0, grand_total_row_index), (-1, grand_total_row_index), FONT_NAME_BOLD), ('BACKGROUND', (0, grand_total_row_index), (-1, grand_total_row_index), colors.lightgrey), ('TEXTCOLOR', (0, grand_total_row_index), (-1, grand_total_row_index), colors.black)]))
    totals_table.wrapOn(c, WIDTH, HEIGHT)
    totals_table_height = totals_table._height
    table_width = 45*mm + 25*mm
    x_position = WIDTH - 20*mm - table_width
    totals_table.drawOn(c, x_position, y_pos - totals_table_height)

    # --- GST Summary Table (Left Side) ---
    tax_summary = {}
    for item in items:
        rate = item['gst_rate']
        taxable_val = (item['quantity'] * item['rate']) * (1 - item['discount_percent'] / 100)
        tax_summary.setdefault(rate, 0)
        tax_summary[rate] += taxable_val
    is_igst = invoice_details['total_igst'] > 0
    if is_igst:
        gst_summary_data = [['Taxable Value', 'IGST Rate', 'IGST Amount']]
        total_taxable_val, total_tax_amt = 0,0
        for rate, taxable_val in sorted(tax_summary.items()):
            tax_amt = taxable_val * (rate / 100)
            gst_summary_data.append([f"{taxable_val:.2f}", f"{rate:.2f}%", f"{tax_amt:.2f}"]); total_taxable_val += taxable_val; total_tax_amt += tax_amt
        gst_summary_data.append([Paragraph(f"<b>{total_taxable_val:.2f}</b>", getSampleStyleSheet()['Normal']), '', Paragraph(f"<b>{total_tax_amt:.2f}</b>", getSampleStyleSheet()['Normal'])])
        gst_summary_table = Table(gst_summary_data, colWidths=[40*mm, 25*mm, 30*mm])
    else:
        gst_summary_data = [['Taxable Value', 'CGST', '', 'SGST', '']]
        gst_summary_data.append(['', 'Rate', 'Amount', 'Rate', 'Amount'])
        total_taxable_val, total_cgst, total_sgst = 0,0,0
        for rate, taxable_val in sorted(tax_summary.items()):
            cgst_amt = taxable_val * (rate / 200); sgst_amt = taxable_val * (rate / 200)
            gst_summary_data.append([f"{taxable_val:.2f}", f"{rate/2:.2f}%", f"{cgst_amt:.2f}", f"{rate/2:.2f}%", f"{sgst_amt:.2f}"]); total_taxable_val += taxable_val; total_cgst += cgst_amt; total_sgst += sgst_amt
        gst_summary_data.append([Paragraph(f"<b>{total_taxable_val:.2f}</b>", getSampleStyleSheet()['Normal']), '', Paragraph(f"<b>{total_cgst:.2f}</b>", getSampleStyleSheet()['Normal']), '', Paragraph(f"<b>{total_sgst:.2f}</b>", getSampleStyleSheet()['Normal'])])
        gst_summary_table = Table(gst_summary_data, colWidths=[35*mm, 15*mm, 20*mm, 15*mm, 20*mm])
        gst_summary_table.setStyle(TableStyle([('SPAN', (1,0), (2,0)), ('SPAN', (3,0), (4,0)), ('ALIGN', (0,0), (-1,0), 'CENTER')]))
    gst_summary_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('FONTNAME', (0,0), (-1,-1), FONT_NAME), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    gst_summary_table.wrapOn(c, WIDTH, HEIGHT)
    gst_summary_table_height = gst_summary_table._height
    
    # --- POSITIONING CHANGE ---
    # The Y-position for the GST table is now calculated based on the position *after* the totals table.
    gst_table_y_pos = y_pos - totals_table_height - 2*mm
    gst_summary_table.drawOn(c, 20*mm, gst_table_y_pos - gst_summary_table_height)

    # --- Footer ---
    # The footer now starts below the lowest of the two tables.
    footer_y_pos = gst_table_y_pos - gst_summary_table_height - 5*mm
    c.setFont(FONT_NAME, 8)
    total_in_words = num2words(int(invoice_details['grand_total']), lang='en_IN').title()
    c.drawString(20 * mm, footer_y_pos, f"Total in Words: Rupees {total_in_words} Only.")
    footer_y_pos -= 5 * mm
    c.line(20 * mm, footer_y_pos, WIDTH - 20 * mm, footer_y_pos); footer_y_pos -= 5 * mm
    c.setFont(FONT_NAME_BOLD, 8); c.drawString(20 * mm, footer_y_pos, "Bank Details:"); c.setFont(FONT_NAME, 8); footer_y_pos -= 4 * mm
    c.drawString(20 * mm, footer_y_pos, f"Bank: {bank_details['bank_name']}"); c.drawString(80 * mm, footer_y_pos, f"A/C No: {bank_details['account_no']}"); footer_y_pos -= 4 * mm
    c.drawString(20 * mm, footer_y_pos, f"Branch: {bank_details['branch']}"); c.drawString(80 * mm, footer_y_pos, f"IFSC: {bank_details['ifsc_code']}")
    footer_y_pos -= 8 * mm
    c.setFont(FONT_NAME_BOLD, 8); c.drawString(20 * mm, footer_y_pos, "Terms & Conditions:"); c.setFont(FONT_NAME, 8); footer_y_pos -= 4 * mm
    terms = invoice_settings['terms_and_conditions'].split('\n')
    for line in terms: c.drawString(20 * mm, footer_y_pos, line); footer_y_pos -= 4 * mm
    c.setFont(FONT_NAME_BOLD, 9); c.drawRightString(WIDTH - 20 * mm, 35 * mm, f"For {company_info['name']}"); c.setFont(FONT_NAME, 9); c.drawRightString(WIDTH - 20 * mm, 20 * mm, "Authorised Signatory")

# The other functions (create_detailed_invoice_report, create_transaction_report_pdf) remain the same
def create_detailed_invoice_report(invoice_ids, settings):
    filename = os.path.join("reports", f"Detailed_Invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    c = canvas.Canvas(filename, pagesize=A4)
    for inv_id in invoice_ids:
        invoice_details, items = db.get_full_invoice_details(inv_id)
        if invoice_details and items:
            draw_invoice_page(c, invoice_details, items, settings['company_info'], settings['bank_details'], settings['invoice_settings'], "for analysis")
            c.showPage()
    c.save()
    print(f"Detailed invoice report saved: {filename}")
    return filename

def create_transaction_report_pdf(invoices, start_date, end_date, settings):
    start_str = start_date.strftime("%b %d, %Y"); end_str = end_date.strftime("%b %d, %Y")
    filename = os.path.join("reports", f"Transaction_Report_{start_date.strftime('%Y_%m_%d')}_to_{end_date.strftime('%Y_%m_%d')}.pdf")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = SimpleDocTemplate(filename, pagesize=landscape(A4), topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet(); styles['Title'].fontName = FONT_NAME_BOLD; styles['h2'].fontName = FONT_NAME; styles['Normal'].fontName = FONT_NAME
    elements = []
    elements.append(Paragraph(settings['company_info']['name'], styles['Title']))
    elements.append(Paragraph("Sales Transaction Report", styles['h2']))
    elements.append(Paragraph(f"Period: {start_str} to {end_str}", styles['h2']))
    elements.append(Spacer(1, 10*mm))
    table_data = [["Inv. ID", "Invoice No.", "Date", "Buyer Name", "Taxable Value (₹)", "Total GST (₹)", "Grand Total (₹)"]]
    total_taxable, total_gst, total_sales = 0.0, 0.0, 0.0
    for inv in invoices:
        table_data.append([inv['id'], inv['invoice_no'], inv['invoice_date'], Paragraph(inv['buyer_name'], styles['Normal']), f"{inv['taxable_value']:.2f}", f"{inv['total_gst']:.2f}", f"{inv['grand_total']:.2f}"])
        total_taxable += inv['taxable_value']; total_gst += inv['total_gst']; total_sales += inv['grand_total']
    table_data.append(["", "", "", Paragraph("<b>TOTALS:</b>", styles['Normal']), Paragraph(f"<b>{total_taxable:.2f}</b>", styles['Normal']), Paragraph(f"<b>{total_gst:.2f}</b>", styles['Normal']), Paragraph(f"<b>{total_sales:.2f}</b>", styles['Normal'])])
    table = Table(table_data, colWidths=[20*mm, 35*mm, 25*mm, 75*mm, 35*mm, 30*mm, 35*mm])
    style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),('TEXTCOLOR', (0, 0), (-1, 0), colors.black),('ALIGN', (0, 0), (-1, -1), 'CENTER'),('ALIGN', (3, 1), (3, -1), 'LEFT'),('ALIGN', (4, 1), (-1, -1), 'RIGHT'),('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),('FONTNAME', (0, 1), (-1, -1), FONT_NAME),('BOTTOMPADDING', (0, 0), (-1, 0), 6),('GRID', (0, 0), (-1, -2), 1, colors.black),('GRID', (3, -1), (-1, -1), 1, colors.black),('BACKGROUND', (0, -1), (2, -1), colors.white),('BACKGROUND', (3, -1), (-1, -1), colors.lightgrey),('VALIGN', (0,0), (-1,-1), 'MIDDLE')])
    table.setStyle(style)
    elements.append(table)
    doc.build(elements)
    print(f"Report saved: {filename}")
    return filename
