

# @csrf_exempt
# @require_POST
# @transaction.atomic
# def save_bill(request):
#     user = request.user
#     fields_will_update = {}
#     system_fields = {}
#     update=False
   
#     try:
#         data = json.loads(request.body.decode("utf-8"))
#     except:
#         return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

#     items = data.get("items", [])
    
#     if not items:
#         return JsonResponse({"success": False, "message": "No items provided"})
    
#     if data.get('voucher_no'):
#         old_bill_no = int(data.get('voucher_no'))
#         old_bill = Invoice.objects.filter(bill_no=old_bill_no ,  user = user)
#         old_header_row = old_bill.filter(header_row = True).first()
#         fields_will_update = {
#             'dateent': old_header_row.dateent,
#             'header_edit_count': old_header_row.header_edit_count + 1,
#             'user': old_header_row.user,
#             "bill_no":old_bill_no,
#         }
#         update = True
#         old_bill.delete()
        
#     else:
#         fields_will_update = {
#             'dateent': now_karachi(),
#             'header_edit_count': 0,
#             'user': user,
#             "bill_no":get_next_voucher('INV'),
#         }

#     system_fields = {
#         "user": user,
#         "company": user.userprofile.company,
#         "branch": user.userprofile.branch,
#         "posterminal": user.userprofile.terminal,
#     }

#     # Build Invoices
#     invoices = []
#     for index,item in enumerate(items):
#         first_item = (index == 0)
#         if first_item:
#             invoices.append(json_to_invoice(item=item, header_fields=data,fields_will_update=fields_will_update,system_fields=system_fields,is_header = True, update = update))
#         else:
#             invoices.append(json_to_invoice(item=item,fields_will_update=fields_will_update,system_fields=system_fields,update=update))
#     Invoice.objects.bulk_create(invoices)

#     #gledg
#     # if data.get('header_total_paid')>0:
#     #     create_gledg_entry(bill_no,net_total,payment_method,user,1,1)

#     return JsonResponse({
#         "success": True,
        
#     })


# class Invoice(models.Model):
#     ver_cntrl = models.CharField(max_length=15)
#     inv_date = models.DateField(blank=True, null=True)
#     bill_no = models.IntegerField(blank=True, null=True)
#     acc_code = models.IntegerField(blank=True, null=True)
#     inv_id = models.IntegerField(db_comment='Refer to Inventory ID')
#     pcs_packing = models.CharField(max_length=15)
#     qty = models.FloatField(blank=True, null=True)
#     retail_price = models.FloatField(blank=True, null=True)
#     item_net_amount = models.FloatField(blank=True, null=True)
#     inv_srno = models.IntegerField(blank=True, null=True)
#     discount = models.FloatField(blank=True, null=True)
#     disc_percent = models.FloatField()
#     disc_flat = models.FloatField()
#     wht = models.FloatField(blank=True, null=True)
#     gst = models.FloatField(blank=True, null=True)
#     dateent = models.DateTimeField(blank=True, null=True)
#     user = models.CharField(max_length=10, blank=True, null=True)
#     branchid = models.IntegerField(blank=True, null=True)
#     remarks = models.TextField(blank=True, null=True)
#     sale_type = models.CharField(max_length=1)
#     tmp_save = models.CharField(max_length=1)
#     show_in_sale_rpt = models.CharField(max_length=1)
#     st_id = models.IntegerField(db_comment='Ref to Store ID')
#     misc_chrgs = models.FloatField()
#     supl_inv_no = models.CharField(max_length=35, db_comment='Ref to Supl. Inv# or  Client PO #')
#     supl_inv_dt = models.DateField(db_comment='Ref to Supl. Inv Date or  Client PO Date')
#     batch_no = models.CharField(max_length=50)
#     expire_dt = models.DateField()
#     item_discount = models.FloatField()
#     item_disc_per = models.FloatField()
#     delivery_person = models.CharField(max_length=15)
#     warranty_print = models.CharField(max_length=200)
#     our_ref = models.CharField(max_length=25)
#     our_date = models.DateField()
#     tran_mode = models.CharField(max_length=10, db_comment='Testing, Checking, Normal')
#     comp_name = models.CharField(max_length=15)
#     rate_cost = models.DecimalField(max_digits=23, decimal_places=14)
#     sales_man = models.CharField(max_length=15)
#     sale_cost = models.DecimalField(max_digits=23, decimal_places=14)
#     paid = models.FloatField()
#     self_trans = models.IntegerField()
#     builty_no = models.CharField(max_length=15)
#     builty_dte = models.DateField()
#     packby = models.CharField(max_length=15)
#     token_no = models.IntegerField()
#     table_name = models.CharField(max_length=15)
#     pur_rate = models.IntegerField()
#     fake_bill_no = models.CharField(max_length=10)
#     station = models.CharField(max_length=5)
#     prod_categ = models.CharField(max_length=25)
#     pack_qty = models.FloatField()
#     pack_qty_rate = models.DecimalField(max_digits=10, decimal_places=2)
#     pctcode = models.CharField(max_length=8)
#     ispra = models.CharField(max_length=1)
#     gst_per = models.FloatField()
#     fbr_inv_no = models.CharField(max_length=30)
#     fbr_posid = models.IntegerField()
#     fbr_buyer = models.CharField(max_length=70)
#     fbr_buyerntn = models.CharField(max_length=9)
#     fbr_buyercnic = models.CharField(max_length=13)
#     fbr_buyerphone = models.CharField(max_length=20)

#     class Meta:
#         managed = False
#         db_table = 'invoice'






# def scan_barcode(request, code):
#     # Ensure the user always has a BarcodConfig
#     config, created = BarcodConfig.objects.get_or_create(
#         user = 'main_bc',
#         defaults={'price_base': 'N'}
#     )
#     # print(request.user)
#     product = None
#     weight_total = None

#     try:
#         # Fast exact match
#         # product = Inventory.objects.filter(
#         #     Q(barcode = str(code)) | Q(inv_id = int(code)) | Q(manualbc__iexact = str(code)) 
#         # ).first()
#         product = Inventory.objects.filter(manualbc__iexact=str(code)).first()

#         if not product:
            
#             product = Inventory.objects.filter(barcode=str(code)).first()
            
#         if not product:
            

#             product = Inventory.objects.filter(inv_id=int(code)).first()

        
            
#         if product:
            

#             return product, None
#     except Exception as e:
#         # Optional: log the exception
#         print(f"Exact match error: {e}")

#     # Weighted barcode
#     if len(code) == config.total_bc_digits:
        
#         try:
#             trimmed = code[config.left_delete:len(code)-config.right_delete]
#             item_code = trimmed[:config.item_bc]
#             w = trimmed[config.item_bc:]
#             kg = w[:config.kg]
#             gr = w[config.kg:config.kg + config.grm]
#             weight_total = Decimal(f'{kg}.{gr}')

#             # Try to find the product by different barcode fields
#             product = Inventory.objects.filter(
#                 barcode=str(item_code)
#             ).first() or Inventory.objects.filter(
#                 manualbc__iexact=str(item_code)
#             ).first() or Inventory.objects.filter(
#                 barcode2__endswith=str(item_code)
#             ).first() or Inventory.objects.filter(
#                 inv_id = int(item_code)
#                 ).first()
            
#         except Exception as e:
#             # Optional: log the exception
#             print(f"Weighted barcode error: {e}")

#     return product, weight_total







# @csrf_exempt
# @require_POST
# @transaction.atomic
# def sync_bills(request):
#     user = request.user
#     if not user.is_authenticated:
#         return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)

#     try:
#         payload = json.loads(request.body.decode("utf-8"))
#     except:
#         return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

#     if not isinstance(payload, list):
#         return JsonResponse({"success": False, "message": "Expected list of bills"}, status=400)

#     synced = []
    
    
  

#     for bill in payload:
#         items = bill.get("items", [])
#         if not items:
#             continue

#         offline_local_id = bill.get('local_id',0)
#         disc_percent = Decimal(bill.get("discountPercent") or 0)
        
#         if disc_percent > Decimal(9.99):
#             return JsonResponse({
#                 "success": False, 
#                 "message": f"Discount percent too high: {disc_percent} In {offline_local_id}. Max allowed: 9.99"
#             }, status=400)

#         delivery_charges = Decimal(bill.get("deliveryCharges") or 0)
#         received_amount = Decimal(bill.get("receivedAmount") or 0)
#         remarks = bill.get("remarks", "")
#         payment_method = bill.get("Payment_method", "cash")

#         item_total = sum(Decimal(i.get("amount") or 0) for i in items)
#         disc_flat = (item_total * disc_percent / 100).quantize(Decimal("0.01"))
#         paymentmethod_detail = bill.get('paymentmethod_detail',"")

#         net_total = item_total-disc_flat+delivery_charges

#         #calling helper fucn
#         bill_no = get_next_bill_no('INV')
#         create_gledg_entry(bill_no, net_total ,payment_method,user,1,1)

#         invoices = []
#         for index,item in enumerate(items):
#             first_item = (index==0)
#             invoice = build_invoice(item, bill_no, disc_percent if first_item else 0, disc_flat if first_item else 0,
#                            delivery_charges if first_item else 0, payment_method, remarks, user.username,
#                            received_amount if first_item else 0 ,paymentmethod_detail)
#             invoices.append(invoice)
#         # invs = [
#         #     build_invoice(item, bill_no, disc_percent, disc_flat,
#         #                   delivery_charges, payment, remarks, user.username,
#         #                   received,paymentmethod_detail)
#         #     for item in items
#         # ]
#         Invoice.objects.bulk_create(invoices)

        
#         synced.append(bill_no)

#     return JsonResponse({"success": True, "synced_bills": synced})

# from django.db import connection
# from decimal import Decimal
# from django.http import JsonResponse

# @require_GET
# def get_bill(request):
#     user = request.user
#     bill_no = request.GET.get("voucher_no")

#     with connection.cursor() as cursor:

#         # 1️⃣ Get latest bill if not provided
#         if not bill_no:
#             cursor.execute("""
#                 SELECT bill_no
#                 FROM invoice
#                 WHERE user = %s
#                 ORDER BY bill_no DESC
#                 LIMIT 1
#             """, [user])

#             row = cursor.fetchone()
#             if not row:
#                 return JsonResponse({"success": False, "message": "No bills found"})
#             bill_no = row[0]



#         # 2️⃣ Fetch everything in ONE query
#         cursor.execute("""
#             SELECT
#                 i.bill_no, i.dateent, i.tran_mode, i.paid,
#                 i.disc_percent, i.disc_flat, i.misc_chrgs,
#                 i.remarks,

#                 i.inv_id, i.qty, i.retail_price,
#                 i.discount, i.item_net_amount,

#                 p.prod_name

#             FROM invoice i
#             LEFT JOIN inventory p ON p.inv_id = i.inv_id
            
#             WHERE i.user = %s AND i.bill_no = %s
#             ORDER BY i.id
#         """, [ user, bill_no])


#         # rc.company_name, rc.logo,
#         #         #         rc.show_header, rc.header_text,
#         #         rc.show_footer, rc.footer_text
# # LEFT JOIN ab_receiptconfig rc ON rc.user_id = %s

#         rows = cursor.fetchall()

#     if not rows:
#         return JsonResponse({"success": False, "message": "Bill not found"})

#     # 3️⃣ Build response (very cheap)
#     total = Decimal("0")
#     items = []

#     for r in rows:
#         amount = Decimal(str(r[12] or 0))
#         total += amount

#         items.append({
#             "id": r[8],
#             "description": r[13] or "Unknown Item",
#             "qty": float(r[9] or 0),
#             "price": float(r[10] or 0),
#             "discount": float(r[11] or 0),
#             "amount": float(amount),
#         })

#     h = rows[0]
#     # print(rows)

#     remarks = h[7]
#     if remarks and remarks.startswith("CC#"):
#         remarks = remarks[8:]

#     net_total = total - Decimal(str(h[5] or 0)) + Decimal(str(h[6] or 0))
#     config = get_receipt_config(request.user)
#     return JsonResponse({
#         "success": True,
#         "voucher_no": h[0],
#         "date": h[1].strftime("%Y-%m-%d %H:%M:%S") if h[1] else None,
#         "remarks": remarks,
#         "item_total": float(total),
#         "net_total": float(net_total),
#         "discount": float(h[5] or 0),
#         "discountPercent": float(h[4] or 0),
#         "delivery_charges": float(h[6] or 0),
#         "received_amount": float(h[3] or 0),
#         "payment_mode": h[2],
#         "items": items,

#         # "company_name": h[14] or "",
#         # "logo": request.build_absolute_uri(h[15]) if h[15] else None,
#         # "show_header": bool(h[16]),
#         # "header_text": h[17] or "",
#         # "show_footer": bool(h[18]),
#         # "footer_text": h[19] or "",
#         "company_name": config.company_name if config else "",
#         "logo": request.build_absolute_uri(config.logo.url) if config and config.logo else None,
#         "show_header": config.show_header if config else False,
#         "header_text": config.header_text if config else "",
#         "show_footer": config.show_footer if config else False,
#         "footer_text": config.footer_text if config else "",
#     })



# def qz_sign(request):
#     msg = request.GET.get("request", "")
#     key_path = os.path.join("static", "private-key.pem")
#     key = RSA.import_key(open(key_path, "rb").read())
#     h = SHA256.new(msg.encode("utf-8"))
#     signature = pkcs1_15.new(key).sign(h)
#     return JsonResponse({"signature": base64.b64encode(signature).decode("utf-8")})

# -----------------------------

# def json_to_invoice(item={}, header_fields={}, fields_will_update={},system_fields={}):
#     fields_to_update = {
#         "bill_no":fields_will_update.get('bill_no'),
#         "dateent":fields_will_update.get('dateent') or now_karachi(),
#         "user":fields_will_update.get('user'),
#         'header_edit_count':fields_will_update.get('edit_count') or 0,
        
#     }

#     header_row = {
#             "is_header":True,

#             # Header totals
#             "header_total_items":header_fields.get('header_total_items', 0),
#             "header_item_total":Decimal(str(header_fields.get('header_item_total', 0))),
#             "header_discount_percent":Decimal(str(header_fields.get('header_discount_percent', 0))),
#             "header_discount_amount":Decimal(str(header_fields.get('header_discount_amount', 0))),
#             "header_delivery_charges":Decimal(str(header_fields.get('header_delivery_charges', 0))),
#             "header_net_total":Decimal(str(header_fields.get('header_net_total', 0))),
#             "header_gst_percent":Decimal(str(header_fields.get('header_gst_percent', 0))),
#             "header_gst_amount":Decimal(str(header_fields.get('header_gst_amount', 0))),
#             "header_msc_charges":Decimal(str(header_fields.get('header_msc_charges', 0))),

#             # Payment
#             "header_payment_mode":header_fields.get('header_payment_mode', 1),
#             "header_cash_paid":Decimal(str(header_fields.get('header_cash_paid', 0))),
#             "header_bank_paid":Decimal(str(header_fields.get('header_bank_paid', 0))),
#             "header_card_last4":header_fields.get('header_card_last4', ''),
#             "header_total_paid":Decimal(str(header_fields.get('header_total_paid', 0))),
#             "header_change_amount":Decimal(str(header_fields.get('header_change_amount', 0))),

#             # Remarks
#             "header_remarks":header_fields.get('header_remarks', ''),

#             "salesman":header_fields.get('salesman') or None,
#         }
    
#     return Invoice(
#         **header_row if header_fields else {},
#         **fields_will_update if fields_will_update else {},
#         bill_no = bill_no,
#         inv_id=item.get('inv_id'),
#         prod_name=item.get('prod_name', ''),
#         category=item.get('category', ''),
#         qty=item.get('qty', 0),
#         rate=item.get('rate', 0),
#         packing_mode=item.get('packing_mode', 1),
#         pack_qty=item.get('pack_qty', 0),
#         row_discount_percent=item.get('row_discount_percent', 0),
#         row_discount_amount=item.get('row_discount_amount', 0),
#         row_net_total=item.get('row_net_total', 0),
#         row_notes=item.get('row_notes', ''),

#         #header common fields
#         dateedit = now_karachi() if fields_will_update else None, 
#         edit_by=user if fields_will_update else None,
        
#         company=system_fields.get('company') or None,
#         branch=system_fields.get('branch') or None,
#         posterminal=system_fields.get('posterminal') or None,
#     )





# def create_gledg_entry(
#         invoice_no,
#         amount,
#         payment_method,        # "CASH" or "BANK"
#         user,
#         branchid,
#         station,
#         prod_categ="Sales",  
#     ):

#     CUSTOMER_ACC = 112000001
#     CASH_ACC     = 110000001
#     BANK_ACC     = 111000001

 
#     if payment_method.lower() == "cash":
#         v_type = "CR"
        
#         dr_account = CASH_ACC
#         cr_account = CUSTOMER_ACC
#         desc1 = f"CR Rcvd against Inv#{invoice_no}"
#         desc2 = f"CR Rcvd against Inv#{invoice_no}"
#         paymentmethod = "Cash"

#     elif payment_method.lower() == "card":
#         v_type = "BR"
        
#         dr_account = BANK_ACC
#         cr_account = CUSTOMER_ACC
#         desc1 = f"BR Rcvd against Inv#{invoice_no}"
#         desc2 = f"BR Rcvd against Inv#{invoice_no}"
#         paymentmethod = "Bank"

#     else:
#         raise ValueError("payment_type must be CASH or BANK")

  
#     vno = get_next_bill_no(v_type)
#     DEFAULT_CHEQUE_DATE = datetime.date(1900, 1, 1)      
#     DEFAULT_DRAWN_BRANCH = ""                            
#     DEFAULT_UPLOAD = "N"
#     DEFAULT_ISPOSTED = "N"
#     DEFAULT_INV_YES_NO = "N"
#     DEFAULT_BANK_RECONCILE = "N"
#     DEFAULT_ACTUAL_INSTALLMENT = 0
#     DEFAULT_PUR_INV = "I"

#     print(now_karachi())
#     entry_cr = Gledg(
#         acc_code=cr_account,
#         ref_acc_code=dr_account,
#         v_type=v_type,
#         vno=vno,
#         date=now_karachi().date(),
#         desc=desc1,
#         remarks="",
#         amount=amount,
#         amt_type="CR",
#         chqno="",
#         # ref_no=invoice_no,
#         dateent=now_karachi(),
#         dateedit=None,
#         user=user,
#         editby="",
#         branchid=branchid,
#         receiptno=None,
#         shift="1",
#         cheque_date=DEFAULT_CHEQUE_DATE,
#         drawn_branch=DEFAULT_DRAWN_BRANCH,
#         paymentmethod=paymentmethod,
#         upload=DEFAULT_UPLOAD,
#         show_in_sale_rpt="N",
#         isposted=DEFAULT_ISPOSTED,
#         inv_yes_no=DEFAULT_INV_YES_NO,
#         bank_reconcile=DEFAULT_BANK_RECONCILE,
#         actual_installment=DEFAULT_ACTUAL_INSTALLMENT,
#         pur_inv=DEFAULT_PUR_INV,
#         station=str(station),
#         prod_categ=prod_categ,
#     )
#     entry_cr.save()

#     entry_dr = Gledg(
#         acc_code=dr_account,
#         ref_acc_code=cr_account,
#         v_type=v_type,
#         vno=vno,
#         date=now_karachi().date(),
#         desc=desc2,
#         remarks="",
#         amount=amount,
#         amt_type="DR",
#         chqno="",
#         # ref_no=invoice_no,
#         dateent=now_karachi(),
#         dateedit=None,
#         user=user,
#         editby="",
#         branchid=branchid,
#         receiptno=None,
#         shift="1",
#         cheque_date=DEFAULT_CHEQUE_DATE,
#         drawn_branch=DEFAULT_DRAWN_BRANCH,
#         paymentmethod=paymentmethod,
#         upload=DEFAULT_UPLOAD,
#         show_in_sale_rpt="N",
#         isposted=DEFAULT_ISPOSTED,
#         inv_yes_no=DEFAULT_INV_YES_NO,
#         bank_reconcile=DEFAULT_BANK_RECONCILE,
#         actual_installment=DEFAULT_ACTUAL_INSTALLMENT,
#         pur_inv=DEFAULT_PUR_INV,
#         station=str(station),
#         prod_categ=prod_categ,
#     )
#     entry_dr.save()

#     return True






# @transaction.atomic
# def get_next_bill_no(type):

#     # LOCK the row in vchno where type='INV'
#     vch = (
#         Vchno.objects
#         .select_for_update()      # <=== THIS LOCKS THE ROW
#         .filter(type=type)
#         .first()
#     )

#     # If row doesn't exist, create & lock it
#     if not vch:
#         vch = Vchno.objects.create(type=type, vchno=0)

#     # Get last bill_no from invoice table
#     last_invoice = Invoice.objects.order_by('-bill_no').first()
#     last_bill_no = last_invoice.bill_no if last_invoice else 0

#     current_vchno = vch.vchno or 0

#     # Compute next bill number (your exact logic)
#     new_bill_no = max(current_vchno, last_bill_no) + 1

#     # Update vchno safely (still locked)
#     vch.vchno = new_bill_no
#     vch.save(fields_will_update=['vchno'])

#     return new_bill_no






























# # -----------------------------
# def build_invoice(item, bill_no, discount_percent, discount_amount,
#                   delivery_charges, payment_method, remarks, user,
#                   received_amount,paymentmethod_detail):

#     qty = Decimal(item.get("qty") or 1)
#     rate = Decimal(item.get("rate") or 0)
#     amount = Decimal(item.get("amount") or (qty * rate))
#     discount= Decimal(item.get('discount') or 0)
#     prod_categ = item.get('prod_categ' or '')
#     return Invoice(
#         bill_no = bill_no,
#         inv_id = Decimal(item.get("id", "0")),
#         qty = qty,
#         retail_price = rate,
#         item_net_amount = amount,
#         prod_categ=prod_categ or 'none',

#         disc_percent=Decimal(discount_percent),
#         disc_flat=Decimal(discount_amount),
#         tran_mode=payment_method,
#         misc_chrgs=delivery_charges,
#         remarks=paymentmethod_detail if paymentmethod_detail else remarks,
#         user=user,
#         dateent=now_karachi(),
#         paid=Decimal(received_amount),

#         acc_code=112000001,
#         ver_cntrl="",
#         pcs_packing="",
#         discount= discount or 0,
#         gst=Decimal(0),
#         item_discount=Decimal(0),
#         item_disc_per=Decimal(0),

#         inv_date=now_karachi().date(),
#         supl_inv_dt=datetime.date(1900, 1, 1) ,
#         supl_inv_no="N/A",
#         batch_no="N/A",
#         expe_dt=datetime.date(1900, 1, 1) ,
#         sale_type="S",
#         tmp_save="N",
#         show_in_sale_rpt="Y",
#         st_id=1,
#         delivery_person="N/A",
#         warranty_print="N/A",
#         our_ref="N/A",
#         our_date=datetime.date(1900, 1, 1) ,
#         comp_name="Finish Product",
#         rate_cost=Decimal(0),
#         sales_man="N/A",
#         sale_cost=Decimal(0),

#         self_trans=0,
#         builty_no="N/A",
#         builty_dte=datetime.date(1900, 1, 1) ,
#         packby="N/A",
#         token_no=0,
#         table_name="N/A",
#         pur_rate=0,
#         fake_bill_no="N/A",
#         station="N/A",
        

#         pack_qty=Decimal(1),
#         pack_qty_rate=Decimal(0),
#         pctcode="N/A",
#         ispra="N",
#         gst_per=Decimal(0),
#         fbr_inv_no="N/A",
#         fbr_posid=0,
#         fbr_buyer="N/A",
#         fbr_buyerntn="N/A",
#         fbr_buyercnic="N/A",
#         fbr_buyerphone="N/A",
#     )




# def get_receipt_config(user):
#     cache_key = f'receipt_config_{user.id}'
#     cfg = cache.get(cache_key)
#     if cfg:
#         last_update = ReceiptConfigurations.objects.filter(user=user).values_list('updated_at',flat=True).first()
#         if last_update and last_update == cfg.updated_at:
#             return cfg
    
#     cfg = ReceiptConfigurations.objects.filter(user = user).first()
#     cache.set("receipt_config", cfg, 300)  # 5 minutes
#     return cfg