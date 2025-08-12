import sqlite3
import os
import shutil
from datetime import datetime

DB_FILE = os.path.join('data', 'billing_app.db')
BACKUP_DIR = 'backups'

def get_db_connection():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, hsn TEXT,
        gst_rate REAL NOT NULL, rate REAL NOT NULL, stock_qty REAL NOT NULL, unit TEXT
    )''')
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN selling_price REAL NOT NULL DEFAULT 0")
    except sqlite3.OperationalError: pass

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, gstin TEXT,
        address TEXT, phone TEXT, email TEXT
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS buyers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, gstin TEXT,
        address TEXT, phone TEXT, email TEXT, state TEXT
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_no TEXT UNIQUE NOT NULL, invoice_date TEXT NOT NULL,
        buyer_id INTEGER, payment_mode TEXT, order_ref TEXT, dispatch_info TEXT,
        subtotal REAL NOT NULL, total_discount REAL NOT NULL, total_gst REAL NOT NULL,
        taxable_value REAL NOT NULL, total_cgst REAL NOT NULL, total_sgst REAL NOT NULL,
        total_igst REAL NOT NULL, freight REAL, round_off REAL, grand_total REAL NOT NULL,
        FOREIGN KEY (buyer_id) REFERENCES buyers (id)
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, product_id INTEGER,
        description TEXT, hsn TEXT, gst_rate REAL, quantity REAL, rate REAL,
        discount_percent REAL, amount REAL,
        FOREIGN KEY (invoice_id) REFERENCES invoices (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT, vendor_id INTEGER NOT NULL, bill_no TEXT,
        purchase_date TEXT, total_amount REAL, amount_paid REAL, payment_status TEXT, notes TEXT,
        FOREIGN KEY (vendor_id) REFERENCES vendors(id)
    )''')
    
    # --- FEATURE: Purchase Payments Table ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchase_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_id INTEGER NOT NULL,
        payment_date TEXT,
        amount REAL,
        payment_mode TEXT,
        reference_no TEXT,
        FOREIGN KEY (purchase_id) REFERENCES purchases(id)
    )''')

    conn.commit()
    conn.close()

# --- FEATURE: Cancel Invoice Function ---
def cancel_invoice(invoice_id):
    """Marks an invoice as cancelled and restores stock."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get items from the invoice to restore stock
        items = cursor.execute("SELECT product_id, quantity FROM invoice_items WHERE invoice_id = ?", (invoice_id,)).fetchall()
        for item in items:
            cursor.execute("UPDATE products SET stock_qty = stock_qty + ? WHERE id = ?", (item['quantity'], item['product_id']))
        
        # Mark invoice as cancelled
        cancelled_prefix = "[CANCELLED] "
        cursor.execute("UPDATE invoices SET grand_total = 0, taxable_value = 0, total_gst = 0, invoice_no = ? || invoice_no WHERE id = ? AND invoice_no NOT LIKE ?", 
                       (cancelled_prefix, invoice_id, f"{cancelled_prefix}%"))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error during cancellation: {e}")
        return False
    finally:
        conn.close()

# --- FEATURE: Purchase Payment Functions ---
def add_purchase_payment(purchase_id, payment_data):
    """Adds a payment record and updates the main purchase entry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Add the new payment record
        cursor.execute('''
            INSERT INTO purchase_payments (purchase_id, payment_date, amount, payment_mode, reference_no)
            VALUES (?, ?, ?, ?, ?)
        ''', (purchase_id, payment_data['payment_date'], payment_data['amount'], payment_data['payment_mode'], payment_data['reference_no']))
        
        # Recalculate total amount paid
        total_paid_result = cursor.execute("SELECT SUM(amount) FROM purchase_payments WHERE purchase_id = ?", (purchase_id,)).fetchone()
        total_paid = total_paid_result[0] if total_paid_result[0] is not None else 0

        # Get total amount of the bill
        purchase = cursor.execute("SELECT total_amount FROM purchases WHERE id = ?", (purchase_id,)).fetchone()
        total_amount = purchase['total_amount']
        
        # Determine new payment status
        status = 'Unpaid'
        if total_amount > 0 and total_paid >= total_amount:
            status = 'Paid'
        elif total_paid > 0:
            status = 'Partial'
        
        # Update the main purchase record
        cursor.execute("UPDATE purchases SET amount_paid = ?, payment_status = ? WHERE id = ?", (total_paid, status, purchase_id))

        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error adding payment: {e}")
        return False
    finally:
        conn.close()

def get_purchase_details(purchase_id):
    """Fetches full details of a single purchase."""
    return execute_query("SELECT p.*, v.name as vendor_name FROM purchases p JOIN vendors v ON p.vendor_id = v.id WHERE p.id = ?", (purchase_id,), fetchone=True)

# [Rest of the file is unchanged]
def get_next_invoice_number(prefix="INV-"):
    conn = get_db_connection(); cursor = conn.cursor()
    cursor.execute("SELECT invoice_no FROM invoices WHERE invoice_no LIKE ? ORDER BY id DESC LIMIT 1", (f"{prefix}%",))
    last_invoice = cursor.fetchone(); conn.close()
    if last_invoice:
        try:
            last_num_str = last_invoice['invoice_no'].split(prefix)[-1]
            if last_num_str.isdigit():
                return f"{prefix}{int(last_num_str) + 1:04d}"
        except (ValueError, TypeError, IndexError): pass
    return f"{prefix}0001"
def save_invoice(invoice_data, items_data):
    conn = get_db_connection(); cursor = conn.cursor()
    taxable_value = invoice_data['subtotal'] - invoice_data['total_discount']
    total_gst = invoice_data['total_cgst'] + invoice_data['total_sgst'] + invoice_data['total_igst']
    try:
        cursor.execute('INSERT INTO invoices (invoice_no, invoice_date, buyer_id, payment_mode, order_ref, dispatch_info, subtotal, total_discount, taxable_value, total_gst, total_cgst, total_sgst, total_igst, freight, round_off, grand_total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',(invoice_data['invoice_no'], invoice_data['invoice_date'], invoice_data['buyer_id'], invoice_data['payment_mode'], invoice_data['order_ref'], invoice_data['dispatch_info'], invoice_data['subtotal'], invoice_data['total_discount'], taxable_value, total_gst, invoice_data['total_cgst'], invoice_data['total_sgst'], invoice_data['total_igst'], invoice_data['freight'], invoice_data['round_off'], invoice_data['grand_total']))
        invoice_id = cursor.lastrowid
        for item in items_data:
            cursor.execute('INSERT INTO invoice_items (invoice_id, product_id, description, hsn, gst_rate, quantity, rate, discount_percent, amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',(invoice_id, item['product_id'], item['description'], item['hsn'], item['gst_rate'], item['quantity'], item['rate'], item['discount_percent'], item['amount']))
            cursor.execute("UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?", (item['quantity'], item['product_id']))
        conn.commit(); return invoice_id
    except sqlite3.Error as e:
        conn.rollback(); print(f"Database error: {e}"); return None
    finally: conn.close()
def get_full_invoice_details(invoice_id):
    conn = get_db_connection(); cursor = conn.cursor()
    invoice_details = cursor.execute('SELECT i.*, b.name as buyer_name, b.gstin as buyer_gstin, b.address as buyer_address, b.state as buyer_state FROM invoices i JOIN buyers b ON i.buyer_id = b.id WHERE i.id = ?', (invoice_id,)).fetchone()
    if not invoice_details: conn.close(); return None, []
    items = cursor.execute('SELECT ii.* FROM invoice_items ii WHERE ii.invoice_id = ?', (invoice_id,)).fetchall()
    conn.close(); return dict(invoice_details), [dict(item) for item in items]
def get_invoices_by_filter(start_date, end_date, buyer_id=None):
    query = 'SELECT i.id, i.invoice_no, i.invoice_date, b.name as buyer_name, i.taxable_value, i.total_gst, i.grand_total FROM invoices i JOIN buyers b ON i.buyer_id = b.id WHERE i.invoice_date BETWEEN ? AND ?'
    params = [start_date, end_date]
    if buyer_id: query += " AND i.buyer_id = ?"; params.append(buyer_id)
    query += " ORDER BY i.invoice_date, i.id"
    return execute_query(query, params, fetchall=True)
def get_all_purchases_with_vendor():
    return execute_query("SELECT p.id, v.name, p.bill_no, p.purchase_date, p.total_amount, p.amount_paid, p.payment_status FROM purchases p JOIN vendors v ON p.vendor_id = v.id ORDER BY p.purchase_date DESC", fetchall=True)
def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_db_connection(); cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if commit: conn.commit(); return cursor.lastrowid
        if fetchone: return cursor.fetchone()
        if fetchall: return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}"); conn.rollback(); return None
    finally: conn.close()
def get_all(table_name): return execute_query(f"SELECT * FROM {table_name} ORDER BY name", fetchall=True)
def get_by_id(table_name, record_id): return execute_query(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,), fetchone=True)
def add_record(table_name, data_dict):
    columns = ', '.join(data_dict.keys()); placeholders = ', '.join(['?'] * len(data_dict))
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    return execute_query(query, tuple(data_dict.values()), commit=True)
def update_record(table_name, record_id, data_dict):
    set_clause = ', '.join([f"{key} = ?" for key in data_dict.keys()])
    query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
    return execute_query(query, tuple(data_dict.values()) + (record_id,), commit=True)
def delete_record(table_name, record_id): execute_query(f"DELETE FROM {table_name} WHERE id = ?", (record_id,), commit=True)
def daily_backup():
    if not os.path.exists(DB_FILE): return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")
    if not os.path.exists(backup_file):
        try:
            shutil.copy2(DB_FILE, backup_file)
            print(f"Database backup created: {backup_file}")
        except Exception as e:
            print(f"Failed to create backup: {e}")