Professional Billing & Inventory Software
A complete and robust desktop-based billing and inventory management application built with Python. This software is designed for Indian Small and Medium-sized Enterprises (SMEs) to handle their day-to-day operations with ease. It features a user-friendly graphical interface and powerful backend logic for GST-compliant invoicing, real-time stock management with cost tracking, comprehensive purchase management, and detailed reporting.

✨ Features
🧾 Billing & Invoicing
GST-Compliant PDF Invoices: Automatically calculates CGST/SGST for intra-state and IGST for inter-state sales.

Professional Layout: Generates clean, professional PDF invoices with your company logo, details, bank information, and terms.

Automatic Buyer Saving: If you enter a new buyer's details while creating an invoice, they are automatically saved to the database for future use.

Multi-Copy Generation: Creates a single PDF file with multiple copies labeled "Original for Recipient," "Duplicate for Transporter," and "Triplicate for Supplier."

📦 Inventory & Stock Management
Centralized Product Database: Manage all your products, including HSN code, GST rate, stock quantity, and units.

Separate Cost vs. Selling Price: Tracks the product's Average Cost Price for internal profit calculation and a separate Selling Price for customers.

Weighted Average Costing (WAC): The system automatically recalculates the average cost price of a product whenever new stock is added at a different rate, ensuring accurate profit margins.

Real-time Stock Deduction: Inventory levels are automatically updated the moment an invoice is saved.

Low-Stock Alerts: Products with stock below a set threshold are visually highlighted in the product list.

🛒 Purchase & Vendor Management
Complete Vendor Database: Maintain a directory of all your vendors with their GSTIN, address, and contact details.

Purchase Bill Tracking: Record all purchase bills from your vendors to manage payables.

Partial Payment Recording: Add multiple partial payments against a single purchase bill until it is fully paid.

Payment References: Record the payment mode (e.g., Cash, Bank Transfer, UPI) and reference numbers (UTR, Cheque No.) for every payment made.

Color-Coded Payment Status: The purchase list uses colors to show the status of each bill (Paid, Partial, Unpaid) at a glance.

🗂️ Reporting & Data Integrity
Comprehensive Transaction History: View, search, and filter your entire sales history.

Cancel & Re-issue Invoices: A safe, accounting-friendly workflow to correct a past invoice. This cancels the original invoice, restores the product stock, and loads the data into the billing tab to be re-issued with a new invoice number.

Multiple PDF Export Options:

Summary Report: Export a filtered list of transactions into a summary PDF.

Detailed Report: Export all invoices from a date range into a single, multi-page PDF file (one page per invoice).

Reprint Any Invoice: Select any past invoice from the reports tab and re-generate its PDF anytime.

⚙️ Usability & Configuration
Fully Graphical Interface: All operations are handled through an intuitive tabbed interface.

Responsive Layout: All tabs, including Billing and Settings, are equipped with scrollbars to ensure usability on smaller monitor resolutions.

Mouse-Wheel Scrolling: Scroll through all lists and tabs using the mouse wheel for faster navigation.

GUI-Based Settings: Easily configure your company details, invoice prefix, and bank details from the Settings tab.

Automatic Daily Backups: The software automatically creates a backup of your database every day in the /backups folder for data safety.

🛠️ Installation
Follow the steps below to set up and run the software on your system.

1. Prerequisites:

Ensure you have Python 3.8 or newer installed on your system.

2. Download the Code:
Download the project files as a ZIP or clone the repository using Git:

Bash

git clone https://github.com/djkalirdp/Professional-Billing-Inventory-Software.git
cd Professional-Billing-Inventory-Software
3. Create a Virtual Environment (Recommended):
This keeps the project's dependencies isolated from other Python projects.

Bash

# Create the virtual environment
python -m venv venv

# Activate the environment
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
4. Install Dependencies:
Install all the required libraries from the requirements.txt file.

Bash

pip install -r requirements.txt
5. Initial Setup:

Create Folders: In the main project directory, create four empty folders: data, invoices, reports, and backups.

Download Font: Search for and download the DejaVuSans.ttf font file. Place it in the main project folder.

Configure Settings: Open the settings.json file and replace the placeholder data with your actual company name, GSTIN, address, bank details, etc.

6. Run the Application:
Once everything is set up, run the following command in your terminal:

Bash

python main.py
📂 File Structure
.
├── main.py                # Main application, GUI, and event handling code
├── database_manager.py    # All functions related to the SQLite database
├── pdf_generator.py       # Logic for creating PDF invoices and reports
├── requirements.txt       # Required Python libraries for pip
├── settings.json          # All user-configurable settings
├── DejaVuSans.ttf         # Font file required for PDF generation
├── data/                  # Stores the SQLite database (.db) file
├── invoices/              # All generated PDF invoices are saved here
├── reports/               # All generated PDF reports are saved here
└── backups/               # Daily database backups are saved here
