import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import webbrowser
from datetime import datetime, timedelta

import database_manager as db
import pdf_generator
from tkcalendar import DateEntry

class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Billing & Inventory Software by Djkali")
        try:
            self.root.state('zoomed')
        except tk.TclError:
            w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.root.geometry(f'{w}x{h}+0+0')

        self.load_settings()
        db.create_tables()
        db.daily_backup()
        self.create_widgets()

    def _on_mousewheel(self, event, canvas):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    def _bind_mousewheel_recursive(self, widget, canvas):
        widget.bind("<MouseWheel>", lambda event, c=canvas: self._on_mousewheel(event, c))
        widget.bind("<Button-4>", lambda event, c=canvas: c.yview_scroll(-1, "units"))
        widget.bind("<Button-5>", lambda event, c=canvas: c.yview_scroll(1, "units"))
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child, canvas)
    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                self.settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            messagebox.showerror("Error", "settings.json is missing or corrupted!")
            self.root.destroy()
    def create_widgets(self):
        style = ttk.Style(self.root); style.theme_use("clam")
        style.configure("TNotebook.Tab", font=('Helvetica', 12, 'bold'), padding=[10, 5])
        style.configure("TButton", font=('Helvetica', 10), padding=5)
        style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
        style.configure("Accent.TButton", foreground="white", background="navy")
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        self.create_billing_tab(); self.create_products_tab(); self.create_buyers_tab()
        self.create_vendors_tab(); self.create_purchases_tab(); self.create_reports_tab()
        self.create_settings_tab()
    
    # [Billing Tab and other unchanged functions are here for completeness]
    # ... The long code blocks for other tabs are correct and don't need to be changed ...
    def create_billing_tab(self):
        self.billing_tab = ttk.Frame(self.notebook); self.notebook.add(self.billing_tab, text='🧾 Billing'); canvas = tk.Canvas(self.billing_tab); scrollbar = ttk.Scrollbar(self.billing_tab, orient="vertical", command=canvas.yview); scrollable_frame = ttk.Frame(canvas); scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width)); canvas.configure(yscrollcommand=scrollbar.set); canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y"); self._bind_mousewheel_recursive(scrollable_frame, canvas); header_frame = ttk.LabelFrame(scrollable_frame, text="Invoice Details", padding=10); header_frame.pack(fill='x', padx=10, pady=5); buyer_frame = ttk.LabelFrame(scrollable_frame, text="Buyer Details", padding=10); buyer_frame.pack(fill='x', padx=10, pady=5); items_frame = ttk.Frame(scrollable_frame); items_frame.pack(fill='both', expand=True, padx=10, pady=5); summary_frame = ttk.LabelFrame(scrollable_frame, text="Summary", padding=10); summary_frame.pack(fill='x', padx=10, pady=5); action_frame = ttk.Frame(scrollable_frame); action_frame.pack(fill='x', pady=10, padx=10); ttk.Label(header_frame, text="Invoice No:").grid(row=0, column=0, padx=5, pady=2, sticky='w'); self.inv_no_var = tk.StringVar(value=db.get_next_invoice_number(self.settings['invoice_settings']['invoice_prefix'])); ttk.Entry(header_frame, textvariable=self.inv_no_var, state='readonly').grid(row=0, column=1, padx=5, pady=2); ttk.Label(header_frame, text="Date:").grid(row=0, column=2, padx=5, pady=2, sticky='w'); self.inv_date_entry = DateEntry(header_frame, date_pattern='yyyy-mm-dd'); self.inv_date_entry.set_date(datetime.now()); self.inv_date_entry.grid(row=0, column=3, padx=5, pady=2); ttk.Label(header_frame, text="Order Ref:").grid(row=1, column=0, padx=5, pady=2, sticky='w'); self.order_ref_var = tk.StringVar(); ttk.Entry(header_frame, textvariable=self.order_ref_var).grid(row=1, column=1, padx=5, pady=2); ttk.Label(header_frame, text="Payment Mode:").grid(row=1, column=2, padx=5, pady=2, sticky='w'); self.payment_mode_var = tk.StringVar(value="Cash"); ttk.Combobox(header_frame, textvariable=self.payment_mode_var, values=["Cash", "Bank Transfer", "UPI", "Cheque"]).grid(row=1, column=3, padx=5, pady=2); ttk.Label(header_frame, text="Dispatch Info:").grid(row=2, column=0, padx=5, pady=2, sticky='w'); self.dispatch_info_var = tk.StringVar(); ttk.Entry(header_frame, textvariable=self.dispatch_info_var).grid(row=2, column=1, columnspan=3, padx=5, pady=2, sticky='ew'); self.buyers = {b['name']: b for b in db.get_all('buyers')}; self.buyer_name_var = tk.StringVar(); self.buyer_gstin_var = tk.StringVar(); self.buyer_address_var = tk.StringVar(); self.buyer_state_var = tk.StringVar(); self.buyer_id_var = tk.IntVar(); ttk.Label(buyer_frame, text="Buyer Name:").grid(row=0, column=0, padx=5, pady=2, sticky='w'); self.buyer_combo = ttk.Combobox(buyer_frame, textvariable=self.buyer_name_var, values=[''] + list(self.buyers.keys())); self.buyer_combo.grid(row=0, column=1, padx=5, pady=2, sticky='ew'); self.buyer_combo.bind("<<ComboboxSelected>>", self.populate_buyer_details); self.buyer_name_var.trace_add("write", self.handle_new_buyer_entry); ttk.Label(buyer_frame, text="GSTIN:").grid(row=0, column=2, padx=5, pady=2, sticky='w'); self.buyer_gstin_entry = ttk.Entry(buyer_frame, textvariable=self.buyer_gstin_var, state='readonly'); self.buyer_gstin_entry.grid(row=0, column=3, padx=5, pady=2, sticky='ew'); ttk.Label(buyer_frame, text="Address:").grid(row=1, column=0, padx=5, pady=2, sticky='w'); self.buyer_address_entry = ttk.Entry(buyer_frame, textvariable=self.buyer_address_var, state='readonly'); self.buyer_address_entry.grid(row=1, column=1, padx=5, pady=2, sticky='ew'); ttk.Label(buyer_frame, text="State:").grid(row=1, column=2, padx=5, pady=2, sticky='w'); self.buyer_state_entry = ttk.Entry(buyer_frame, textvariable=self.buyer_state_var, state='readonly'); self.buyer_state_entry.grid(row=1, column=3, padx=5, pady=2, sticky='ew'); buyer_frame.grid_columnconfigure(1, weight=1); buyer_frame.grid_columnconfigure(3, weight=1); self.item_entries = []; self.item_frame_canvas = tk.Canvas(items_frame); scrollbar_items_y = ttk.Scrollbar(items_frame, orient="vertical", command=self.item_frame_canvas.yview); scrollbar_items_x = ttk.Scrollbar(items_frame, orient="horizontal", command=self.item_frame_canvas.xview); self.scrollable_items_frame = ttk.Frame(self.item_frame_canvas); self.scrollable_items_frame.bind("<Configure>", lambda e: self.item_frame_canvas.configure(scrollregion=self.item_frame_canvas.bbox("all"))); self.item_frame_canvas.create_window((0, 0), window=self.scrollable_items_frame, anchor="nw"); self.item_frame_canvas.configure(yscrollcommand=scrollbar_items_y.set, xscrollcommand=scrollbar_items_x.set); scrollbar_items_y.pack(side="right", fill="y"); scrollbar_items_x.pack(side="bottom", fill="x"); self.item_frame_canvas.pack(side="left", fill="both", expand=True); self._bind_mousewheel_recursive(self.scrollable_items_frame, self.item_frame_canvas); headers = ["S.No", "Product", "HSN", "GST%", "Qty", "Unit", "Rate", "Discount %", "Amount"];
        for i, header in enumerate(headers): ttk.Label(self.scrollable_items_frame, text=header, font=('Helvetica', 10, 'bold')).grid(row=0, column=i, padx=5, pady=5)
        self.products = {p['name']: p for p in db.get_all('products')}; self.add_invoice_item_row(); item_buttons_frame = ttk.Frame(scrollable_frame); item_buttons_frame.pack(fill='x', padx=10, pady=(0,5)); ttk.Button(item_buttons_frame, text="+ Add Row", command=self.add_invoice_item_row).pack(side='left', padx=5); ttk.Button(item_buttons_frame, text="- Remove Row", command=self.remove_invoice_item_row).pack(side='left', padx=5); self.subtotal_var=tk.DoubleVar(); self.total_discount_var=tk.DoubleVar(); self.total_cgst_var=tk.DoubleVar(); self.total_sgst_var=tk.DoubleVar(); self.total_igst_var=tk.DoubleVar(); self.freight_var=tk.DoubleVar(value=0.0); self.grand_total_var=tk.DoubleVar(); self.round_off_var=tk.DoubleVar(); summary_labels=["Subtotal:","Total Discount:","CGST:","SGST:","IGST:","Freight:","Round Off:","GRAND TOTAL:"]; summary_vars=[self.subtotal_var,self.total_discount_var,self.total_cgst_var,self.total_sgst_var,self.total_igst_var,self.freight_var,self.round_off_var,self.grand_total_var];
        for i, (label,var) in enumerate(zip(summary_labels,summary_vars)):
            ttk.Label(summary_frame,text=label).grid(row=i,column=2,padx=10,pady=2,sticky='e'); entry = ttk.Entry(summary_frame,textvariable=var,state='readonly',justify='right',font=('Helvetica',10,'bold'));
            if label == "Freight:": entry.config(state='normal'); entry.bind("<KeyRelease>",self.update_summary)
            entry.grid(row=i,column=3,padx=10,pady=2,sticky='w')
        ttk.Button(action_frame, text="💾 Save & Generate PDF", command=self.save_and_generate_invoice, style="Accent.TButton").pack(side='right', padx=5); ttk.Button(action_frame, text="🔄 Clear Form", command=self.clear_invoice_form).pack(side='right', padx=5)
    def add_invoice_item_row(self):
        row_index=len(self.item_entries)+1;row_widgets={};s_no_label=ttk.Label(self.scrollable_items_frame,text=f"{row_index}.");s_no_label.grid(row=row_index,column=0,padx=5,pady=2);row_widgets['s_no_label']=s_no_label;product_var=tk.StringVar();product_combo=ttk.Combobox(self.scrollable_items_frame,textvariable=product_var,values=list(self.products.keys()),width=40);product_combo.grid(row=row_index,column=1,padx=5,pady=2);product_combo.bind("<<ComboboxSelected>>",lambda e,r=row_index: self.populate_product_details(r));product_combo.bind("<KeyRelease>",lambda e,r=row_index: self.update_summary());row_widgets['product_var']=product_var;row_widgets['product_combo']=product_combo;cols=['hsn','gst_rate','qty','unit','rate','discount','amount'];widths=[10,5,8,8,10,8,12];
        for i,col_name in enumerate(cols):
            var=tk.StringVar(value='0.0' if col_name in ['qty','rate','discount','amount'] else '');entry=ttk.Entry(self.scrollable_items_frame,textvariable=var,width=widths[i],justify='right');
            if col_name in ['hsn','gst_rate','unit','amount']:entry.config(state='readonly')
            else:entry.bind("<KeyRelease>",lambda e,r=row_index: self.update_summary())
            entry.grid(row=row_index,column=i+2,padx=5,pady=2);row_widgets[f'{col_name}_var']=var;row_widgets[f'{col_name}_entry']=entry
        self.item_entries.append(row_widgets)
    def remove_invoice_item_row(self):
        if len(self.item_entries)>1:row_to_remove=self.item_entries.pop();[widget.destroy() for widget in row_to_remove.values() if isinstance(widget,tk.Widget)];self.update_summary()
    def populate_product_details(self,row_index):
        row_widgets=self.item_entries[row_index-1];product_name=row_widgets['product_var'].get();product_data=self.products.get(product_name);
        if product_data:row_widgets['hsn_var'].set(product_data['hsn']);row_widgets['gst_rate_var'].set(f"{product_data['gst_rate']:.2f}");row_widgets['rate_var'].set(f"{product_data['selling_price']:.2f}");row_widgets['unit_var'].set(product_data['unit']);row_widgets['qty_var'].set("1.0");row_widgets['discount_var'].set("0.0");row_widgets['qty_entry'].focus()
        self.update_summary()
    def set_buyer_fields_state(self,state):self.buyer_gstin_entry.config(state=state);self.buyer_address_entry.config(state=state);self.buyer_state_entry.config(state=state)
    def populate_buyer_details(self,event=None):
        buyer_name=self.buyer_name_var.get();buyer_data=self.buyers.get(buyer_name);
        if buyer_data:self.buyer_id_var.set(buyer_data['id']);self.buyer_gstin_var.set(buyer_data['gstin']);self.buyer_address_var.set(buyer_data['address']);self.buyer_state_var.set(buyer_data['state']);self.set_buyer_fields_state('readonly')
        self.update_summary()
    def handle_new_buyer_entry(self,*args):
        buyer_name=self.buyer_name_var.get();
        if buyer_name not in self.buyers:
            if self.buyer_id_var.get()!=0:self.buyer_id_var.set(0);self.buyer_gstin_var.set("");self.buyer_address_var.set("");self.buyer_state_var.set("")
            self.set_buyer_fields_state('normal')
    def update_summary(self,event=None):
        subtotal,total_discount,total_cgst,total_sgst,total_igst=0.0,0.0,0.0,0.0,0.0;seller_state_gst_code=self.settings['company_info']['gstin'][:2];buyer_gstin=self.buyer_gstin_var.get();buyer_state_gst_code=buyer_gstin[:2] if buyer_gstin else "";is_igst=bool(buyer_gstin) and (seller_state_gst_code.lower()!=buyer_state_gst_code.lower());
        for row in self.item_entries:
            try:
                qty=float(row['qty_var'].get() or 0);rate=float(row['rate_var'].get() or 0);discount_percent=float(row['discount_var'].get() or 0);gst_rate=float(row['gst_rate_var'].get() or 0);base_amount=qty*rate;discount_amount=base_amount*(discount_percent/100);taxable_amount=base_amount-discount_amount;row['amount_var'].set(f"{taxable_amount:.2f}");subtotal+=base_amount;total_discount+=discount_amount;gst_amount=taxable_amount*(gst_rate/100);
                if is_igst:total_igst+=gst_amount
                else:total_cgst+=gst_amount/2;total_sgst+=gst_amount/2
            except (ValueError,KeyError):continue
        self.subtotal_var.set(round(subtotal,2));self.total_discount_var.set(round(total_discount,2));self.total_cgst_var.set(round(total_cgst,2));self.total_sgst_var.set(round(total_sgst,2));self.total_igst_var.set(round(total_igst,2));
        try:freight=self.freight_var.get()
        except tk.TclError:freight=0.0
        grand_total=(subtotal-total_discount)+total_cgst+total_sgst+total_igst+freight;rounded_total=round(grand_total);round_off=rounded_total-grand_total;self.grand_total_var.set(rounded_total);self.round_off_var.set(round(round_off,2))
    def clear_invoice_form(self):
        self.inv_no_var.set(db.get_next_invoice_number(self.settings['invoice_settings']['invoice_prefix']));self.order_ref_var.set("");self.dispatch_info_var.set("");self.payment_mode_var.set("Bank Transfer");self.inv_date_entry.set_date(datetime.now());self.buyer_name_var.set('');self.buyer_gstin_var.set('');self.buyer_address_var.set('');self.buyer_state_var.set('');self.buyer_id_var.set(0);self.set_buyer_fields_state('readonly');
        while len(self.item_entries)>1:self.remove_invoice_item_row()
        first_row=self.item_entries[0];
        for key,widget in first_row.items():
            if 'var' in key:widget.set("")
        self.freight_var.set(0.0);self.update_summary()
    def save_and_generate_invoice(self):
        buyer_name=self.buyer_name_var.get().strip();
        if not buyer_name:messagebox.showerror("Validation Error","Buyer name cannot be empty.");return
        buyer_id=0;existing_buyer=self.buyers.get(buyer_name);
        if existing_buyer:buyer_id=existing_buyer['id']
        else:
            new_buyer_data={"name":buyer_name,"gstin":self.buyer_gstin_var.get().strip(),"address":self.buyer_address_var.get().strip(),"phone":"","email":"","state":self.buyer_state_var.get().strip()};
            if not new_buyer_data['address'] or not new_buyer_data['state']:messagebox.showerror("Validation Error","For a new buyer, please fill in GSTIN, Address, and State.");return
            buyer_id=db.add_record('buyers',new_buyer_data);
            if not buyer_id:messagebox.showerror("Database Error","Failed to save the new buyer.");return
            self.refresh_buyer_data()
        invoice_data={'invoice_no':self.inv_no_var.get(),'invoice_date':self.inv_date_entry.get_date().strftime('%Y-%m-%d'),'buyer_id':buyer_id,'payment_mode':self.payment_mode_var.get(),'order_ref':self.order_ref_var.get(),'dispatch_info':self.dispatch_info_var.get(),'subtotal':self.subtotal_var.get(),'total_discount':self.total_discount_var.get(),'total_cgst':self.total_cgst_var.get(),'total_sgst':self.total_sgst_var.get(),'total_igst':self.total_igst_var.get(),'freight':self.freight_var.get(),'round_off':self.round_off_var.get(),'grand_total':self.grand_total_var.get()};items_data=[];
        for row in self.item_entries:
            product_name=row['product_var'].get();
            if not product_name:continue
            product_info=self.products.get(product_name);
            if not product_info:messagebox.showerror("Validation Error",f"Product '{product_name}' not found in database.");return
            try:
                qty=float(row['qty_var'].get() or 0);
                if qty<=0:continue
                if product_info['stock_qty']<qty:
                    if not messagebox.askyesno("Stock Alert",f"Not enough stock for '{product_name}'.\nAvailable: {product_info['stock_qty']}\nRequired: {qty}\n\nContinue anyway?"):return
                items_data.append({'product_id':product_info['id'],'description':product_name,'hsn':row['hsn_var'].get(),'gst_rate':float(row['gst_rate_var'].get() or 0),'quantity':qty,'rate':float(row['rate_var'].get() or 0),'discount_percent':float(row['discount_var'].get() or 0),'amount':float(row['amount_var'].get() or 0)})
            except (ValueError,KeyError) as e:messagebox.showerror("Validation Error",f"Invalid data in an item row: {e}");return
        if not items_data:messagebox.showerror("Validation Error","Cannot save an invoice with no items.");return
        invoice_id=db.save_invoice(invoice_data,items_data);
        if not invoice_id:messagebox.showerror("Database Error","Failed to save the invoice.");return
        full_invoice_details,full_items=db.get_full_invoice_details(invoice_id);
        if full_invoice_details:
            pdf_filename=pdf_generator.create_invoice_pdf(full_invoice_details,full_items,self.settings);messagebox.showinfo("Success",f"Invoice #{invoice_id} saved and PDF generated.");
            if messagebox.askyesno("Open PDF","Do you want to open the generated invoice PDF?"):webbrowser.open(os.path.realpath(pdf_filename))
        else:messagebox.showerror("Error","Could not retrieve saved invoice data for PDF generation.")
        self.clear_invoice_form();self.refresh_product_data()
    def create_products_tab(self):
        self.products_tab=ttk.Frame(self.notebook);self.notebook.add(self.products_tab,text='📦 Products');top_frame=ttk.Frame(self.products_tab);top_frame.pack(fill='x',padx=10,pady=10);ttk.Label(top_frame,text="Search:").pack(side='left',padx=(0,5));self.product_search_var=tk.StringVar();self.product_search_var.trace("w",lambda *args:self.search_records(self.product_tree,'products',self.product_search_var.get()));ttk.Entry(top_frame,textvariable=self.product_search_var,width=40).pack(side='left',padx=5);ttk.Button(top_frame,text="🔄 Refresh",command=self.refresh_product_data).pack(side='left',padx=5);ttk.Button(top_frame,text="❌ Delete Selected",command=self.delete_product).pack(side='right',padx=5);ttk.Button(top_frame,text="✏️ Edit/Update Stock",command=self.edit_product).pack(side='right',padx=5);ttk.Button(top_frame,text="➕ Add New Product",command=self.add_product).pack(side='right',padx=5);tree_frame=ttk.Frame(self.products_tab);tree_frame.pack(fill='both',expand=True,padx=10,pady=5);cols=('id','name','hsn','gst_rate','selling_price','stock_qty','unit');self.product_tree=ttk.Treeview(tree_frame,columns=cols,show='headings',selectmode='browse');self.product_tree.heading('id',text='ID');self.product_tree.heading('name',text='Product Name');self.product_tree.heading('hsn',text='HSN/SAC');self.product_tree.heading('gst_rate',text='GST %');self.product_tree.heading('selling_price',text='Selling Price (₹)');self.product_tree.heading('stock_qty',text='Stock Qty');self.product_tree.heading('unit',text='Unit');self.product_tree.column('id',width=50,anchor='center');self.product_tree.column('name',width=300);self.product_tree.column('hsn',width=100,anchor='center');self.product_tree.column('gst_rate',width=80,anchor='e');self.product_tree.column('selling_price',width=120,anchor='e');self.product_tree.column('stock_qty',width=100,anchor='e');self.product_tree.column('unit',width=80,anchor='center');ysb=ttk.Scrollbar(tree_frame,orient='vertical',command=self.product_tree.yview);xsb=ttk.Scrollbar(tree_frame,orient='horizontal',command=self.product_tree.xview);self.product_tree.configure(yscrollcommand=ysb.set,xscrollcommand=xsb.set);ysb.pack(side='right',fill='y');xsb.pack(side='bottom',fill='x');self.product_tree.pack(fill='both',expand=True);self.product_tree.tag_configure('low_stock',background='orange');self.refresh_product_data()
    def refresh_product_data(self):
        for item in self.product_tree.get_children():self.product_tree.delete(item)
        all_products=db.get_all('products');
        for prod in all_products:
            tags=('low_stock',) if prod['stock_qty']<=10 else ();values=(prod['id'],prod['name'],prod['hsn'],f"{prod['gst_rate']:.2f}",f"{prod['selling_price']:.2f}",prod['stock_qty'],prod['unit']);self.product_tree.insert('','end',values=values,tags=tags)
        self.products={p['name']:p for p in all_products};
        if hasattr(self,'item_entries'):
            for row in self.item_entries:row['product_combo']['values']=list(self.products.keys())
    def add_product(self):self.show_product_dialog('Add New Product')
    def edit_product(self):
        selected_item=self.product_tree.focus();
        if not selected_item:messagebox.showwarning("Selection Error","Please select a product to edit.");return
        self.show_product_dialog('Edit Product/Update Stock',record_id=self.product_tree.item(selected_item)['values'][0])
    def delete_product(self):
        selected_item=self.product_tree.focus();
        if not selected_item:messagebox.showwarning("Selection Error","Please select a product to delete.");return
        item_values=self.product_tree.item(selected_item)['values'];
        if messagebox.askyesno("Confirm Delete",f"Are you sure you want to delete '{item_values[1]}'?"):db.delete_record('products',item_values[0]);self.refresh_product_data();messagebox.showinfo("Success",f"Product '{item_values[1]}' deleted.")
    def show_product_dialog(self,title,record_id=None):
        dialog=tk.Toplevel(self.root);dialog.title(title);dialog.transient(self.root);dialog.grab_set();main_frame=ttk.Frame(dialog,padding=10);main_frame.pack(expand=True,fill="both");entries={};record_data=db.get_by_id('products',record_id) if record_id else None;info_frame=ttk.LabelFrame(main_frame,text="Product Information",padding=10);info_frame.pack(fill="x",expand=True,pady=5);base_fields=['name','hsn','gst_rate','unit'];
        for i,field in enumerate(base_fields):ttk.Label(info_frame,text=f"{field.replace('_',' ').title()}:").grid(row=i,column=0,padx=5,pady=2,sticky='w');var=tk.StringVar(value=record_data[field] if record_data else '');entry=ttk.Entry(info_frame,textvariable=var,width=40);entry.grid(row=i,column=1,padx=5,pady=2,sticky='ew');entries[field]=var
        ttk.Label(info_frame,text="Selling Price (₹):").grid(row=len(base_fields),column=0,padx=5,pady=2,sticky='w');selling_price_var=tk.DoubleVar(value=record_data['selling_price'] if record_data else 0.0);entry=ttk.Entry(info_frame,textvariable=selling_price_var,width=40);entry.grid(row=len(base_fields),column=1,padx=5,pady=2,sticky='ew');entries['selling_price']=selling_price_var;stock_frame=ttk.LabelFrame(main_frame,text="Stock & Cost Management (Owner View)",padding=10);stock_frame.pack(fill="x",expand=True,pady=5);ttk.Label(stock_frame,text="Current Stock:").grid(row=0,column=0,sticky='w',padx=5,pady=2);current_stock_var=tk.DoubleVar(value=record_data['stock_qty'] if record_data else 0.0);ttk.Label(stock_frame,textvariable=current_stock_var,font=('Helvetica',10,'bold')).grid(row=0,column=1,sticky='w',padx=5,pady=2);ttk.Label(stock_frame,text="Average Cost Price:").grid(row=1,column=0,sticky='w',padx=5,pady=2);current_rate_var=tk.StringVar(value=f"₹ {record_data['rate']:.2f}" if record_data else "₹ 0.00");ttk.Label(stock_frame,textvariable=current_rate_var,font=('Helvetica',10,'bold')).grid(row=1,column=1,sticky='w',padx=5,pady=2);ttk.Separator(stock_frame,orient='horizontal').grid(row=2,column=0,columnspan=2,sticky='ew',pady=10);ttk.Label(stock_frame,text="Add New Stock Qty:").grid(row=3,column=0,sticky='w',padx=5,pady=2);add_stock_var=tk.DoubleVar(value=0.0);entries['add_stock']=add_stock_var;ttk.Entry(stock_frame,textvariable=add_stock_var,width=15).grid(row=3,column=1,sticky='w',padx=5,pady=2);ttk.Label(stock_frame,text="Purchase Rate (for new stock):").grid(row=4,column=0,sticky='w',padx=5,pady=2);purchase_rate_var=tk.DoubleVar(value=0.0);entries['purchase_rate']=purchase_rate_var;ttk.Entry(stock_frame,textvariable=purchase_rate_var,width=15).grid(row=4,column=1,sticky='w',padx=5,pady=2);
        def save():
            data={field:var.get() for field,var in entries.items() if isinstance(var,tk.StringVar)};
            try:added_stock=entries['add_stock'].get();purchase_rate=entries['purchase_rate'].get();data['gst_rate']=float(data.get('gst_rate',0));data['selling_price']=entries['selling_price'].get()
            except(ValueError,tk.TclError):messagebox.showerror("Invalid Input","Please enter valid numbers.",parent=dialog);return
            final_data={};
            if record_id:
                current_stock=record_data['stock_qty'];current_cost_price=record_data['rate'];
                if added_stock>0:old_value=current_stock*current_cost_price;new_value=added_stock*purchase_rate;new_total_stock=current_stock+added_stock;new_avg_cost=(old_value+new_value)/new_total_stock if new_total_stock>0 else 0;final_data['stock_qty']=new_total_stock;final_data['rate']=new_avg_cost
                else:final_data['stock_qty']=current_stock;final_data['rate']=current_cost_price
                final_data.update(data);db.update_record('products',record_id,final_data)
            else:final_data=data;final_data['stock_qty']=added_stock;final_data['rate']=purchase_rate;db.add_record('products',final_data)
            self.refresh_product_data();dialog.destroy()
        ttk.Button(main_frame,text="Save Product",command=save,style="Accent.TButton").pack(pady=10)
    def create_buyers_tab(self): self.buyers_tab = ttk.Frame(self.notebook); self.notebook.add(self.buyers_tab, text='🧑‍🌾 Buyers'); self.create_generic_crud_tab(self.buyers_tab, 'buyers', ['id', 'name', 'gstin', 'address', 'phone', 'email', 'state'])
    def create_vendors_tab(self): self.vendors_tab = ttk.Frame(self.notebook); self.notebook.add(self.vendors_tab, text='🚚 Vendors'); self.create_generic_crud_tab(self.vendors_tab, 'vendors', ['id', 'name', 'gstin', 'address', 'phone', 'email'])
    def refresh_buyer_data(self):
        self.refresh_generic_tree('buyers'); self.buyers = {b['name']: b for b in db.get_all('buyers')}
        self.buyer_combo['values'] = [""] + list(self.buyers.keys())
        if hasattr(self, 'report_buyer_combo'): self.report_buyer_combo['values'] = ["All Buyers"] + list(self.buyers.keys())
    def refresh_vendor_data(self):
        self.refresh_generic_tree('vendors')
        if hasattr(self, 'purchase_vendor_combo'):
             self.vendors = {v['name']: v for v in db.get_all('vendors')}
             self.purchase_vendor_combo['values'] = list(self.vendors.keys())
    def create_purchases_tab(self):
        self.purchases_tab = ttk.Frame(self.notebook, padding=10); self.notebook.add(self.purchases_tab, text='🛒 Purchases')
        form_frame = ttk.LabelFrame(self.purchases_tab, text="Add/Edit Purchase Bill", padding=10); form_frame.pack(fill='x', pady=5)
        self.purchase_vars = {}
        ttk.Label(form_frame, text="Vendor:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.vendors = {v['name']: v for v in db.get_all('vendors')}
        vendor_var = tk.StringVar(); self.purchase_vars['vendor_id'] = vendor_var
        self.purchase_vendor_combo = ttk.Combobox(form_frame, textvariable=vendor_var, values=list(self.vendors.keys()), width=30)
        self.purchase_vendor_combo.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(form_frame, text="Purchase Date:").grid(row=0, column=2, sticky='w', padx=5, pady=2)
        date_var = DateEntry(form_frame, date_pattern='yyyy-mm-dd'); date_var.set_date(datetime.now()); self.purchase_vars['purchase_date'] = date_var
        date_var.grid(row=0, column=3, padx=5, pady=2)
        ttk.Label(form_frame, text="Bill No:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        bill_var = tk.StringVar(); self.purchase_vars['bill_no'] = bill_var
        ttk.Entry(form_frame, textvariable=bill_var).grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(form_frame, text="Total Amount (₹):").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        total_var = tk.DoubleVar(); self.purchase_vars['total_amount'] = total_var
        ttk.Entry(form_frame, textvariable=total_var).grid(row=1, column=3, padx=5, pady=2)
        ttk.Label(form_frame, text="Amount Paid (₹):").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        paid_var = tk.DoubleVar(); self.purchase_vars['amount_paid'] = paid_var
        ttk.Entry(form_frame, textvariable=paid_var).grid(row=2, column=1, padx=5, pady=2)
        action_frame = ttk.Frame(form_frame); action_frame.grid(row=2, column=3, sticky='e', padx=5, pady=5)
        ttk.Button(action_frame, text="Save Purchase", command=self.save_purchase).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Clear", command=self.clear_purchase_form).pack(side='left', padx=5)
        
        # --- Treeview and Add Payment button ---
        tree_frame_container = ttk.Frame(self.purchases_tab)
        tree_frame_container.pack(fill='both', expand=True, pady=10)
        
        tree_frame = ttk.LabelFrame(tree_frame_container, text="Purchase History", padding=10)
        tree_frame.pack(fill='both', expand=True)
        
        cols = ('id', 'vendor', 'bill_no', 'date', 'total', 'paid', 'due', 'status')
        self.purchase_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse')
        for col in cols: self.purchase_tree.heading(col, text=col.replace('_', ' ').title())
        self.purchase_tree.column('id', width=40); self.purchase_tree.column('vendor', width=200); self.purchase_tree.column('bill_no', width=120); self.purchase_tree.column('date', width=100); self.purchase_tree.column('total', width=100, anchor='e'); self.purchase_tree.column('paid', width=100, anchor='e'); self.purchase_tree.column('due', width=100, anchor='e'); self.purchase_tree.column('status', width=100, anchor='center');
        ysb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.purchase_tree.yview); ysb.pack(side='right', fill='y')
        self.purchase_tree.configure(yscrollcommand=ysb.set); self.purchase_tree.pack(fill='both', expand=True)
        self.purchase_tree.tag_configure('unpaid', background='#FFCCCC'); self.purchase_tree.tag_configure('partial', background='#FFFFCC')

        # --- FEATURE: Add Payment Button ---
        ttk.Button(tree_frame_container, text="Add Payment to Selected Bill", command=self.show_add_payment_dialog).pack(pady=5)
        self.refresh_purchases_tree()

    def clear_purchase_form(self):
        self.purchase_vars['vendor_id'].set(''); self.purchase_vars['bill_no'].set(''); self.purchase_vars['purchase_date'].set_date(datetime.now()); self.purchase_vars['total_amount'].set(0.0); self.purchase_vars['amount_paid'].set(0.0)
    
    def save_purchase(self):
        vendor_name = self.purchase_vars['vendor_id'].get()
        if not vendor_name: messagebox.showerror("Error", "Please select a vendor."); return
        vendor_data = self.vendors.get(vendor_name)
        if not vendor_data: messagebox.showerror("Error", "Invalid vendor selected."); return
        vendor_id = vendor_data['id']
        try:
            total_amount = self.purchase_vars['total_amount'].get(); initial_paid = self.purchase_vars['amount_paid'].get()
        except (ValueError, tk.TclError): messagebox.showerror("Error", "Please enter valid numbers for amounts."); return
        status = 'Unpaid'
        if total_amount > 0 and initial_paid >= total_amount: status = 'Paid'
        elif initial_paid > 0: status = 'Partial'
        
        purchase_data = {'vendor_id': vendor_id, 'bill_no': self.purchase_vars['bill_no'].get(), 'purchase_date': self.purchase_vars['purchase_date'].get_date().strftime('%Y-%m-%d'), 'total_amount': total_amount, 'amount_paid': initial_paid, 'payment_status': status, 'notes': ''}
        purchase_id = db.add_record('purchases', purchase_data)
        
        if purchase_id and initial_paid > 0:
            payment_data = {'payment_date': purchase_data['purchase_date'], 'amount': initial_paid, 'payment_mode': 'Cash', 'reference_no': 'Initial Payment'}
            db.add_purchase_payment(purchase_id, payment_data)

        self.refresh_purchases_tree(); self.clear_purchase_form()
    
    def refresh_purchases_tree(self):
        for item in self.purchase_tree.get_children(): self.purchase_tree.delete(item)
        records = db.get_all_purchases_with_vendor()
        if not records: return
        for rec in records:
            due = rec['total_amount'] - rec['amount_paid']
            tags = ('unpaid',) if rec['payment_status'] == 'Unpaid' else ('partial',) if rec['payment_status'] == 'Partial' else ()
            self.purchase_tree.insert('', 'end', values=(rec['id'], rec['name'], rec['bill_no'], rec['purchase_date'], f"{rec['total_amount']:.2f}", f"{rec['amount_paid']:.2f}", f"{due:.2f}", rec['payment_status']), tags=tags)

    def show_add_payment_dialog(self):
        selected_item = self.purchase_tree.focus()
        if not selected_item: messagebox.showwarning("Selection Error", "Please select a purchase bill to add a payment."); return
        
        purchase_id = self.purchase_tree.item(selected_item)['values'][0]
        purchase_data = db.get_purchase_details(purchase_id)
        if not purchase_data: messagebox.showerror("Error", "Could not fetch purchase details."); return

        due_amount = purchase_data['total_amount'] - purchase_data['amount_paid']
        if due_amount <= 0: messagebox.showinfo("Payment Info", "This bill is already fully paid."); return

        dialog = tk.Toplevel(self.root); dialog.title("Add Payment"); dialog.transient(self.root); dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(expand=True, fill="both")
        
        ttk.Label(frame, text=f"Vendor: {purchase_data['vendor_name']}").grid(row=0, column=0, columnspan=2, sticky='w', pady=2)
        ttk.Label(frame, text=f"Bill No: {purchase_data['bill_no']}").grid(row=1, column=0, columnspan=2, sticky='w', pady=2)
        ttk.Label(frame, text=f"Amount Due: ₹ {due_amount:.2f}", font=('Helvetica', 10, 'bold')).grid(row=2, column=0, columnspan=2, sticky='w', pady=5)
        
        ttk.Label(frame, text="Payment Date:").grid(row=3, column=0, sticky='w', pady=5)
        payment_date_entry = DateEntry(frame, date_pattern='yyyy-mm-dd'); payment_date_entry.set_date(datetime.now())
        payment_date_entry.grid(row=3, column=1, sticky='ew', pady=5)

        ttk.Label(frame, text="Amount to Pay (₹):").grid(row=4, column=0, sticky='w', pady=5)
        amount_var = tk.DoubleVar(value=due_amount)
        ttk.Entry(frame, textvariable=amount_var).grid(row=4, column=1, sticky='ew', pady=5)

        ttk.Label(frame, text="Payment Mode:").grid(row=5, column=0, sticky='w', pady=5)
        mode_var = tk.StringVar(value="Bank Transfer")
        ttk.Combobox(frame, textvariable=mode_var, values=["Cash", "Bank Transfer", "UPI", "Cheque"]).grid(row=5, column=1, sticky='ew', pady=5)

        ttk.Label(frame, text="Reference No (UTR, etc.):").grid(row=6, column=0, sticky='w', pady=5)
        ref_var = tk.StringVar()
        ttk.Entry(frame, textvariable=ref_var).grid(row=6, column=1, sticky='ew', pady=5)

        def save_payment():
            try:
                pay_amount = amount_var.get()
                if not (0 < pay_amount <= due_amount):
                    messagebox.showerror("Invalid Amount", f"Payment must be between 0 and the due amount of {due_amount:.2f}", parent=dialog)
                    return
            except (ValueError, tk.TclError): messagebox.showerror("Invalid Input", "Please enter a valid payment amount.", parent=dialog); return
            
            payment_data = {
                'payment_date': payment_date_entry.get_date().strftime('%Y-%m-%d'),
                'amount': pay_amount,
                'payment_mode': mode_var.get(),
                'reference_no': ref_var.get()
            }
            if db.add_purchase_payment(purchase_id, payment_data):
                messagebox.showinfo("Success", "Payment added successfully.")
                self.refresh_purchases_tree()
                dialog.destroy()
            else:
                messagebox.showerror("Database Error", "Failed to add payment.", parent=dialog)

        ttk.Button(frame, text="Save Payment", command=save_payment, style="Accent.TButton").grid(row=7, column=0, columnspan=2, pady=10)

    def create_reports_tab(self):
        self.reports_tab = ttk.Frame(self.notebook); self.notebook.add(self.reports_tab, text='🗂️ Reports')
        filter_frame = ttk.LabelFrame(self.reports_tab, text="Filters", padding=10); filter_frame.pack(fill='x', padx=10, pady=10)
        ttk.Label(filter_frame, text="From Date:").grid(row=0, column=0, padx=5, pady=5); self.report_from_date = DateEntry(filter_frame, date_pattern='yyyy-mm-dd'); self.report_from_date.set_date(datetime.now() - timedelta(days=30)); self.report_from_date.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(filter_frame, text="To Date:").grid(row=0, column=2, padx=5, pady=5); self.report_to_date = DateEntry(filter_frame, date_pattern='yyyy-mm-dd'); self.report_to_date.set_date(datetime.now()); self.report_to_date.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(filter_frame, text="Buyer:").grid(row=0, column=4, padx=5, pady=5); self.report_buyer_var = tk.StringVar(value="All Buyers"); self.report_buyer_combo = ttk.Combobox(filter_frame, textvariable=self.report_buyer_var, width=30); self.report_buyer_combo.grid(row=0, column=5, padx=5, pady=5)
        ttk.Button(filter_frame, text="🔍 Apply Filter", command=self.apply_report_filter).grid(row=0, column=6, padx=20, pady=5)
        result_frame = ttk.Frame(self.reports_tab); result_frame.pack(fill='both', expand=True, padx=10, pady=5)
        cols = ('id', 'invoice_no', 'invoice_date', 'buyer_name', 'taxable_value', 'total_gst', 'grand_total'); self.report_tree = ttk.Treeview(result_frame, columns=cols, show='headings', selectmode='browse')
        for col in cols: self.report_tree.heading(col, text=col.replace('_', ' ').title())
        self.report_tree.column('id', width=50, anchor='center'); self.report_tree.column('invoice_no', width=150); self.report_tree.column('invoice_date', width=100, anchor='center'); self.report_tree.column('buyer_name', width=250); self.report_tree.column('taxable_value', width=120, anchor='e'); self.report_tree.column('total_gst', width=120, anchor='e'); self.report_tree.column('grand_total', width=120, anchor='e');
        ysb = ttk.Scrollbar(result_frame, orient='vertical', command=self.report_tree.yview); xsb = ttk.Scrollbar(result_frame, orient='horizontal', command=self.report_tree.xview); self.report_tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set); ysb.pack(side='right', fill='y'); xsb.pack(side='bottom', fill='x'); self.report_tree.pack(fill='both', expand=True)
        export_frame = ttk.Frame(self.reports_tab); export_frame.pack(fill='x', padx=10, pady=10)
        # --- FEATURE: Cancel & Re-issue Button ---
        ttk.Button(export_frame, text="✏️ Cancel & Re-issue Selected Invoice", command=self.cancel_and_reissue_invoice).pack(side='left', padx=10)
        ttk.Button(export_frame, text="📄 Export Summary PDF", command=self.export_summary_report).pack(side='right', padx=5)
        ttk.Button(export_frame, text="📑 Export Detailed Invoices PDF", command=self.export_detailed_report).pack(side='right', padx=5)
        self.refresh_buyer_data(); self.apply_report_filter()

    def cancel_and_reissue_invoice(self):
        selected_item = self.report_tree.focus()
        if not selected_item: messagebox.showwarning("Selection Error", "Please select an invoice from the list to cancel and re-issue."); return
        
        invoice_no = self.report_tree.item(selected_item)['values'][1]
        if "[CANCELLED]" in invoice_no: messagebox.showerror("Error", "This invoice is already cancelled."); return

        if not messagebox.askyesno("Confirm Action", f"Are you sure you want to cancel Invoice {invoice_no}?\n\nThis will:\n1. Mark the old invoice as CANCELLED.\n2. Restore the sold stock to inventory.\n3. Load its data into the Billing tab to create a new, editable invoice.\n\nThis action cannot be undone."):
            return

        inv_id = self.report_tree.item(selected_item)['values'][0]
        
        # 1. Get old data BEFORE cancelling
        old_invoice_details, old_items = db.get_full_invoice_details(inv_id)
        if not old_invoice_details: messagebox.showerror("Error", "Could not fetch details of the invoice to be cancelled."); return

        # 2. Cancel the invoice in DB (restores stock, renames invoice)
        if not db.cancel_invoice(inv_id): messagebox.showerror("Database Error", "Failed to cancel the invoice in the database."); return
        
        messagebox.showinfo("Success", f"Invoice {invoice_no} has been cancelled. Its data is now loaded in the Billing tab for re-issue.")

        # 3. Load data to Billing tab
        self.clear_invoice_form()
        self.inv_no_var.set(db.get_next_invoice_number(self.settings['invoice_settings']['invoice_prefix'])) # Set a NEW invoice number
        
        # Load buyer
        self.buyer_combo.set(old_invoice_details['buyer_name'])
        self.populate_buyer_details()
        
        # Load other details
        self.inv_date_entry.set_date(datetime.strptime(old_invoice_details['invoice_date'], '%Y-%m-%d'))
        self.order_ref_var.set(old_invoice_details.get('order_ref', ''))
        self.dispatch_info_var.set(old_invoice_details.get('dispatch_info', ''))
        self.payment_mode_var.set(old_invoice_details.get('payment_mode', 'Bank Transfer'))
        self.freight_var.set(old_invoice_details.get('freight', 0.0))

        # Load items
        while len(self.item_entries) < len(old_items): self.add_invoice_item_row()
        while len(self.item_entries) > len(old_items): self.remove_invoice_item_row()
        
        for i, item in enumerate(old_items):
            row_widgets = self.item_entries[i]
            row_widgets['product_var'].set(item['description'])
            self.populate_product_details(i + 1) # This will fill HSN, GST, etc.
            row_widgets['qty_var'].set(item['quantity'])
            row_widgets['rate_var'].set(item['rate'])
            row_widgets['discount_var'].set(item['discount_percent'])
        
        self.update_summary() # Recalculate totals
        self.notebook.select(self.billing_tab) # Switch to billing tab
        self.apply_report_filter() # Refresh report list

    # [Rest of the file is unchanged]
    def apply_report_filter(self):
        start_date = self.report_from_date.get_date().strftime('%Y-%m-%d'); end_date = self.report_to_date.get_date().strftime('%Y-%m-%d')
        buyer_name = self.report_buyer_var.get(); buyer_id = None
        if buyer_name != "All Buyers":
            if buyer_data := self.buyers.get(buyer_name): buyer_id = buyer_data['id']
        self.filtered_invoices = db.get_invoices_by_filter(start_date, end_date, buyer_id)
        for item in self.report_tree.get_children(): self.report_tree.delete(item)
        if self.filtered_invoices:
            for inv in self.filtered_invoices:
                values = (inv['id'], inv['invoice_no'], inv['invoice_date'], inv['buyer_name'], f"{inv['taxable_value']:.2f}", f"{inv['total_gst']:.2f}", f"{inv['grand_total']:.2f}")
                self.report_tree.insert('', 'end', values=values)
    def export_summary_report(self):
        if not hasattr(self, 'filtered_invoices') or not self.filtered_invoices: messagebox.showinfo("No Data", "There is no data to export."); return
        start_date = self.report_from_date.get_date(); end_date = self.report_to_date.get_date()
        try:
            pdf_filename = pdf_generator.create_transaction_report_pdf(self.filtered_invoices, start_date, end_date, self.settings)
            messagebox.showinfo("Success", f"Summary Report PDF generated successfully.");
            if messagebox.askyesno("Open PDF", "Do you want to open the report?"): webbrowser.open(os.path.realpath(pdf_filename))
        except Exception as e: messagebox.showerror("Error", f"Failed to generate PDF: {e}")
    def regenerate_selected_invoice(self):
        selected_item = self.report_tree.focus()
        if not selected_item: messagebox.showwarning("Selection Error", "Please select an invoice from the list to re-generate."); return
        inv_id = self.report_tree.item(selected_item)['values'][0]
        full_details, items = db.get_full_invoice_details(inv_id)
        if full_details:
            pdf_filename = pdf_generator.create_invoice_pdf(full_details, items, self.settings)
            messagebox.showinfo("Success", f"Invoice PDF re-generated successfully.")
            if messagebox.askyesno("Open PDF", "Do you want to open the invoice?"): webbrowser.open(os.path.realpath(pdf_filename))
        else: messagebox.showerror("Error", "Could not find invoice details.")
    def export_detailed_report(self):
        if not hasattr(self, 'filtered_invoices') or not self.filtered_invoices: messagebox.showinfo("No Data", "There is no data to export."); return
        invoice_ids = [inv['id'] for inv in self.filtered_invoices]
        try:
            pdf_filename = pdf_generator.create_detailed_invoice_report(invoice_ids, self.settings)
            messagebox.showinfo("Success", "Detailed Invoices PDF generated successfully.")
            if messagebox.askyesno("Open PDF", "Do you want to open the combined report?"): webbrowser.open(os.path.realpath(pdf_filename))
        except Exception as e: messagebox.showerror("Error", f"Failed to generate detailed PDF: {e}")
    def create_settings_tab(self):
        self.settings_tab = ttk.Frame(self.notebook); self.notebook.add(self.settings_tab, text='⚙️ Settings'); canvas = tk.Canvas(self.settings_tab); scrollbar = ttk.Scrollbar(self.settings_tab, orient="vertical", command=canvas.yview); scrollable_frame = ttk.Frame(canvas, padding=20); scrollable_frame.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all"))); canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width)); canvas.configure(yscrollcommand=scrollbar.set); canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y"); self._bind_mousewheel_recursive(scrollable_frame, canvas); self.settings_vars = {}; company_frame = ttk.LabelFrame(scrollable_frame, text="Company Information", padding=10); company_frame.pack(fill='x', pady=5); c_info=self.settings['company_info'];self.settings_vars['company_info']={};fields=["name","gstin","pan","address_line1","address_line2","phone","email","website"];
        for i,field in enumerate(fields): ttk.Label(company_frame,text=f"{field.replace('_',' ').title()}:").grid(row=i,column=0,sticky='w',padx=5,pady=2);var=tk.StringVar(value=c_info.get(field,''));ttk.Entry(company_frame,textvariable=var,width=60).grid(row=i,column=1,sticky='ew',padx=5,pady=2);self.settings_vars['company_info'][field]=var
        bank_frame=ttk.LabelFrame(scrollable_frame, text="Bank Details", padding=10);bank_frame.pack(fill='x',pady=10);b_info=self.settings['bank_details'];self.settings_vars['bank_details']={};fields=["bank_name","account_no","ifsc_code","branch"];
        for i,field in enumerate(fields): ttk.Label(bank_frame,text=f"{field.replace('_',' ').title()}:").grid(row=i,column=0,sticky='w',padx=5,pady=2);var=tk.StringVar(value=b_info.get(field,''));ttk.Entry(bank_frame,textvariable=var,width=60).grid(row=i,column=1,sticky='ew',padx=5,pady=2);self.settings_vars['bank_details'][field]=var
        invoice_frame=ttk.LabelFrame(scrollable_frame, text="Invoice Settings", padding=10);invoice_frame.pack(fill='x',pady=5);i_info=self.settings['invoice_settings'];self.settings_vars['invoice_settings']={};ttk.Label(invoice_frame,text="Invoice Prefix:").grid(row=0,column=0,sticky='w',padx=5,pady=2);prefix_var=tk.StringVar(value=i_info.get('invoice_prefix',''));ttk.Entry(invoice_frame,textvariable=prefix_var,width=60).grid(row=0,column=1,sticky='ew',padx=5,pady=2);self.settings_vars['invoice_settings']['invoice_prefix']=prefix_var;ttk.Label(invoice_frame,text="Terms & Conditions:").grid(row=1,column=0,sticky='nw',padx=5,pady=2);terms_var=tk.Text(invoice_frame,height=4,width=60);terms_var.insert('1.0',i_info.get('terms_and_conditions',''));terms_var.grid(row=1,column=1,sticky='ew',padx=5,pady=2);self.settings_vars['invoice_settings']['terms_and_conditions']=terms_var
        ttk.Button(scrollable_frame, text="Save All Settings", command=self.update_and_save_settings,style="Accent.TButton").pack(pady=20)
    def save_settings(self):
        try:
            with open('settings.json','w') as f: json.dump(self.settings,f,indent=2)
            messagebox.showinfo("Success","Settings saved successfully.")
            self.load_settings(); self.clear_invoice_form()
        except Exception as e: messagebox.showerror("Error",f"Failed to save settings: {e}")
    def update_and_save_settings(self):
        for section, fields in self.settings_vars.items():
            for field, var in fields.items():
                if isinstance(var, tk.Text): self.settings[section][field] = var.get('1.0', 'end-1c')
                else: self.settings[section][field] = var.get()
        self.save_settings()
    def create_generic_crud_tab(self, parent_tab, table_name, columns):
        top_frame=ttk.Frame(parent_tab);top_frame.pack(fill='x',padx=10,pady=10)
        search_var=tk.StringVar();search_var.trace("w",lambda *args:self.search_records(tree,table_name,search_var.get()));ttk.Label(top_frame,text="Search:").pack(side='left',padx=(0,5));ttk.Entry(top_frame,textvariable=search_var,width=40).pack(side='left',padx=5)
        refresh_func=getattr(self,f"refresh_{table_name[:-1]}_data",lambda: self.refresh_generic_tree(table_name));ttk.Button(top_frame,text="🔄 Refresh",command=refresh_func).pack(side='left',padx=5);ttk.Button(top_frame,text="❌ Delete Selected",command=lambda: self.delete_generic_record(tree,table_name)).pack(side='right',padx=5);ttk.Button(top_frame,text="✏️ Edit Selected",command=lambda: self.edit_generic_record(tree,table_name)).pack(side='right',padx=5);ttk.Button(top_frame,text=f"➕ Add New {table_name[:-1].title()}",command=lambda: self.show_record_dialog(table_name,f'Add New {table_name[:-1].title()}')).pack(side='right',padx=5)
        tree_frame=ttk.Frame(parent_tab);tree_frame.pack(fill='both',expand=True,padx=10,pady=5);tree=ttk.Treeview(tree_frame,columns=columns,show='headings',selectmode='browse')
        for col in columns:tree.heading(col,text=col.replace('_',' ').title());tree.column(col,width=150)
        tree.column('id',width=50,anchor='center');ysb=ttk.Scrollbar(tree_frame,orient='vertical',command=tree.yview);xsb=ttk.Scrollbar(tree_frame,orient='horizontal',command=tree.xview);tree.configure(yscrollcommand=ysb.set,xscrollcommand=xsb.set);ysb.pack(side='right',fill='y');xsb.pack(side='bottom',fill='x');tree.pack(fill='both',expand=True);setattr(self,f"{table_name}_tree",tree);refresh_func()
    def refresh_generic_tree(self,table_name):
        tree=getattr(self,f"{table_name}_tree");
        for item in tree.get_children():tree.delete(item)
        records = db.get_all(table_name)
        if records:
            for record in records:tree.insert('', 'end', values=tuple(record))
    def search_records(self,tree,table_name,search_term):
        for item in tree.get_children():tree.delete(item)
        query = f"SELECT * FROM {table_name} WHERE name LIKE ? OR hsn LIKE ?" if table_name == 'products' else f"SELECT * FROM {table_name} WHERE name LIKE ?"
        params = (f'%{search_term}%', f'%{search_term}%') if table_name == 'products' else (f'%{search_term}%',)
        if records := db.execute_query(query,params,fetchall=True):
            for record in records:tree.insert('', 'end', values=tuple(record))
    def show_record_dialog(self,table_name,title,record_id=None):
        if table_name == 'products': self.show_product_dialog(title, record_id); return
        dialog=tk.Toplevel(self.root);dialog.title(title);dialog.transient(self.root);dialog.grab_set()
        fields={'buyers':['name','gstin','address','phone','email','state'],'vendors':['name','gstin','address','phone','email']}.get(table_name,[])
        entries={};record_data=db.get_by_id(table_name,record_id) if record_id else None
        for i,field in enumerate(fields):
            ttk.Label(dialog,text=f"{field.replace('_',' ').title()}:").grid(row=i,column=0,padx=10,pady=5,sticky='e');var=tk.StringVar(value=record_data[field] if record_data else '');entry=ttk.Entry(dialog,textvariable=var,width=40);entry.grid(row=i,column=1,padx=10,pady=5);entries[field]=var
        def save():
            data={field:var.get() for field,var in entries.items()};
            if record_id:db.update_record(table_name,record_id,data)
            else:db.add_record(table_name,data)
            refresh_func=getattr(self,f"refresh_{table_name[:-1]}_data",lambda: self.refresh_generic_tree(table_name));refresh_func();dialog.destroy()
        ttk.Button(dialog,text="Save",command=save).grid(row=len(fields),column=0,columnspan=2,pady=10)
    def edit_generic_record(self,tree,table_name):
        if not (selected_item:=tree.focus()):messagebox.showwarning("Selection Error",f"Please select a {table_name[:-1]} to edit.");return
        self.show_record_dialog(table_name,f'Edit {table_name[:-1].title()}',record_id=tree.item(selected_item)['values'][0])
    def delete_generic_record(self,tree,table_name):
        if not (selected_item:=tree.focus()):messagebox.showwarning("Selection Error",f"Please select a {table_name[:-1]} to delete.");return
        item_values=tree.item(selected_item)['values']
        if messagebox.askyesno("Confirm Delete",f"Are you sure you want to delete '{item_values[1]}'?"):
            db.delete_record(table_name,item_values[0]);refresh_func=getattr(self,f"refresh_{table_name[:-1]}_data",lambda:self.refresh_generic_tree(table_name));refresh_func();messagebox.showinfo("Success",f"{table_name[:-1].title()} '{item_values[1]}' deleted.")

if __name__ == "__main__":
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()