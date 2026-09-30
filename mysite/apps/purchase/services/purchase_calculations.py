
from decimal import Decimal



from decimal import Decimal, ROUND_HALF_UP


D = lambda v: Decimal(str(v or 0))

def calculate_purchase_row(item):
    qty = D(item.get("qty")) # this is number of packs user entered
    rate = D(item.get("rate")) # rate per PACK if mode 2,3, else per base
    packing_mode = int(item.get("packing_mode", 1))
    pack_qty = D(item.get("pack_qty", 1)) or Decimal('1')
    bonus = D(item.get("row_bonus", 0)) # bonus always in BASE units

    # 1. Base qty
    if packing_mode in [2, 3]: # carton / dozen
        base_qty = qty * pack_qty
    else:
        base_qty = qty
        pack_qty = Decimal('1') # normalize

    # 2. Gross - rate is per pack for mode 2,3
    gross = qty * rate

    # 3. Discounts
    disc1_p = D(item.get("row_discount_percent"))
    disc1_a = D(item.get("row_discount_amount"))
    if disc1_a == 0 and disc1_p > 0:
        disc1_a = gross * disc1_p / Decimal('100')

    disc2_p = D(item.get("row_discount_percent2", 0))
    disc2_a = D(item.get("row_discount_amount2", 0))
    if disc2_a == 0 and disc2_p > 0:
        disc2_a = (gross - disc1_a) * disc2_p / Decimal('100')

    net_total = gross - disc1_a - disc2_a
    eff_base_qty = base_qty + bonus

    return {
        "qty": qty,
        "base_qty": base_qty,
        "eff_base_qty": eff_base_qty,
        "rate": rate,
        "pack_qty": pack_qty,
        "packing_mode": packing_mode,
        "bonus": bonus,
        "gross_total": gross,
        "row_discount_percent": disc1_p,
        "row_discount_amount": disc1_a,
        "row_discount_percent2": disc2_p,
        "row_discount_amount2": disc2_a,
        "row_net_total": net_total,
    }

def calculate_landed_cost(cart_items, header_fields):
    rows = [calculate_purchase_row(it) for it in cart_items]
    total_net = sum((r["row_net_total"] for r in rows), Decimal('0'))
    total_net_safe = total_net if total_net != 0 else Decimal('1')

    total_addon = D(header_fields.get("header_freight_amount")) + D(header_fields.get("header_unload_amount")) + \
                  D(header_fields.get("header_labour_amount")) + D(header_fields.get("header_msc_charges")) + \
                  D(header_fields.get("header_gst_amount")) + D(header_fields.get("header_wht_amount")) + \
                  D(header_fields.get("header_advtax_amount")) + D(header_fields.get("header_delivery_charges"))

    total_header_disc = D(header_fields.get("header_discount_amount"))

    final_rows = []
    for r in rows:
        ratio = r["row_net_total"] / total_net_safe
        row_landed_total = r["row_net_total"] + (total_addon * ratio) - (total_header_disc * ratio)

        # COST PER BASE UNIT - THIS IS YOUR INVENTORY COST
        if r["eff_base_qty"] > 0:
            cost_per_base = row_landed_total / r["eff_base_qty"]
        else:
            cost_per_base = Decimal('0')

        # COST PER PACK - for display
        cost_per_pack = cost_per_base * r["pack_qty"]

        r["row_landed_total"] = row_landed_total.quantize(Decimal('0.01'), ROUND_HALF_UP)
        r["row_total_cost"] = cost_per_base.quantize(Decimal('0.001'), ROUND_HALF_UP) # per base unit
        r["row_total_cost_per_pack"] = cost_per_pack.quantize(Decimal('0.01'), ROUND_HALF_UP)
        final_rows.append(r)

    return final_rows




# D = lambda v: Decimal(str(v or 0))

# def calculate_purchase_row(item):
#     qty = D(item.get("qty"))
#     rate = D(item.get("rate"))
#     pack_qty = D(item.get("pack_qty", 1)) or Decimal('1')
    
#     # If rate is per pack, convert to base qty rate. If your rate is already per base, remove this
#     # gross = qty * rate * pack_qty
#     gross = qty * rate  # assuming rate is per base unit

#     disc1_p = D(item.get("row_discount_percent"))
#     disc1_a = D(item.get("row_discount_amount"))
#     if disc1_a == 0 and disc1_p > 0:
#         disc1_a = gross * disc1_p / Decimal('100')

#     disc2_p = D(item.get("row_discount_percent2", 0))
#     disc2_a = D(item.get("row_discount_amount2", 0))
#     after_disc1 = gross - disc1_a
#     if disc2_a == 0 and disc2_p > 0:
#         disc2_a = after_disc1 * disc2_p / Decimal('100')

#     net_total = gross - disc1_a - disc2_a
    
#     # Effective qty for costing
#     bonus = D(item.get("row_bonus", 0))

#     return {
#         "qty": qty,
#         "rate": rate,
#         "pack_qty": pack_qty,
#         "bonus": bonus,
#         "eff_qty": qty + bonus,
#         "gross_total": gross,
#         "row_discount_percent": disc1_p,
#         "row_discount_amount": disc1_a,
#         "row_discount_percent2": disc2_p,
#         "row_discount_amount2": disc2_a,
#         "row_net_total": net_total,
#     }



# def calculate_landed_cost(cart_items, header_fields):
#     # Pass 1: calc rows and total base
#     rows = [calculate_purchase_row(it) for it in cart_items]
#     total_net = sum((r["row_net_total"] for r in rows), Decimal('0'))
#     total_qty = sum((r["qty"] for r in rows), Decimal('0'))
    
#     # Avoid div by zero
#     total_net_safe = total_net if total_net != 0 else Decimal('1')

#     # Header addon pools
#     freight = D(header_fields.get("header_freight_amount"))
#     unload = D(header_fields.get("header_unload_amount"))
#     labour = D(header_fields.get("header_labour_amount"))
#     msc = D(header_fields.get("header_msc_charges"))
#     gst = D(header_fields.get("header_gst_amount"))
#     wht = D(header_fields.get("header_wht_amount"))
#     advtax = D(header_fields.get("header_advtax_amount"))
#     delivery = D(header_fields.get("header_delivery_charges"))
#     shortaccess = D(header_fields.get("header_shortaccess", 0))

#     total_addon = freight + unload + labour + msc + gst + wht + advtax + delivery + shortaccess
#     total_header_disc = D(header_fields.get("header_discount_amount"))

#     # Pass 2: allocate
#     final_rows = []
#     for r in rows:
#         # PROFESSIONAL: Allocation by Value. Best for accounting
#         ratio = r["row_net_total"] / total_net_safe

#         allocated_addon = total_addon * ratio
#         allocated_disc = total_header_disc * ratio

#         row_landed_total = r["row_net_total"] + allocated_addon - allocated_disc
        
#         # Per unit landed cost
#         if r["eff_qty"] > 0:
#             per_unit_cost = row_landed_total / r["eff_qty"]
#         else:
#             per_unit_cost = Decimal('0')

#         # Optional: if you want weight-based allocation for freight only
#         # if header_fields.get("header_weight") and total_qty > 0:
#         #    weight_ratio = r["qty"] / total_qty
#         #    freight_alloc = freight * weight_ratio
#         #    ...

#         r["row_landed_total"] = row_landed_total.quantize(Decimal('0.01'), ROUND_HALF_UP)

#         r["row_total_cost"]  = (per_unit_cost / (r.get('pack_qty',1) * r.get('qty',1)) if r.get('packing_mode') in [2,3] else per_unit_cost / r.get('qty',1)).quantize(Decimal('0.0001'), ROUND_HALF_UP)
        
#         r["allocated_addon"] = allocated_addon
#         r["allocated_discount"] = allocated_disc
#         final_rows.append(r)

#     return final_rows


# def calculate_row_totals(item):
#     """
#     Calculate a single invoice row.
#     """

#     qty = Decimal(str(item.get("qty", 0)))
#     rate = Decimal(str(item.get("rate", 0)))

#     gross_total = qty * rate

#     discount_percent = Decimal(
#         str(item.get("row_discount_percent", 0))
#     )

#     discount_amount = Decimal(
#         str(item.get("row_discount_amount", 0))
#     )

#     # Calculate amount from percent if amount not supplied
#     if discount_amount == 0 and discount_percent > 0:
#         discount_amount = (
#             gross_total * discount_percent
#         ) / Decimal("100")

#     net_total = gross_total - discount_amount

#     return {
#         "qty": qty,
#         "rate": rate,
#         "row_discount_percent": discount_percent,
#         "row_discount_amount": discount_amount,
#         "row_net_total": net_total,
#     }





# def calculate_header_totals(header_fields, items):
#     """
#     Calculate invoice header totals from detail rows.
#     """

#     item_total = Decimal("0")

#     for item in items:
#         row = calculate_row_totals(item)
#         item_total += row["row_net_total"]

#     total_items = len(items)

#     discount_percent = Decimal(
#         str(header_fields.get("header_discount_percent", 0))
#     )

#     discount_amount = Decimal(
#         str(header_fields.get("header_discount_amount", 0))
#     )

#     if discount_amount == 0 and discount_percent > 0:
#         discount_amount = (
#             item_total * discount_percent
#         ) / Decimal("100")

#     delivery_charges = Decimal(
#         str(header_fields.get("header_delivery_charges", 0))
#     )

#     gst_percent = Decimal(
#         str(header_fields.get("header_gst_percent", 0))
#     )

#     taxable_amount = (
#         item_total
#         - discount_amount
#         + delivery_charges
#     )

#     gst_amount = Decimal(
#         str(header_fields.get("header_gst_amount", 0))
#     )

#     if gst_amount == 0 and gst_percent > 0:
#         gst_amount = (
#             taxable_amount * gst_percent
#         ) / Decimal("100")

#     msc_charges = Decimal(
#         str(header_fields.get("header_msc_charges", 0))
#     )

#     net_total = (
#         taxable_amount
#         + gst_amount
#         + msc_charges
#     )

#     cash_paid = Decimal(
#         str(header_fields.get("header_cash_paid", 0))
#     )

#     bank_paid = Decimal(
#         str(header_fields.get("header_bank_paid", 0))
#     )

#     total_paid = Decimal(int(cash_paid) + int(bank_paid))

#     change_amount = max(
#         Decimal("0"),
#         total_paid - net_total
#     )

#     return {
#         "header_total_items": total_items,
#         "header_item_total": item_total,
#         "header_discount_percent": discount_percent,
#         "header_discount_amount": discount_amount,
#         "header_delivery_charges": delivery_charges,
#         "header_gst_percent": gst_percent,
#         "header_gst_amount": gst_amount,
#         "header_msc_charges": msc_charges,
#         "header_net_total": net_total,
#         "header_cash_paid": cash_paid,
#         "header_bank_paid": bank_paid,
#         "header_total_paid": total_paid,
#         "header_change_amount": change_amount,
#     }







# # def scan_barcode(request, code):
# #     # Ensure the user always has a BarcodConfig
# #     config, created = BarcodConfig.objects.get_or_create(
# #         user = 'main_bc',
# #         defaults={'price_base': 'N'}
# #     )
# #     # print(request.user)
# #     product = None
# #     weight_total = None

# #     try:
# #         # Fast exact match
# #         # product = Inventory.objects.filter(
# #         #     Q(barcode = str(code)) | Q(inv_id = int(code)) | Q(manualbc__iexact = str(code)) 
# #         # ).first()
# #         product = Inventory.objects.filter(manualbc__iexact=str(code)).first()

# #         if not product:
            
# #             product = Inventory.objects.filter(barcode=str(code)).first()
            
# #         if not product:
            

# #             product = Inventory.objects.filter(inv_id=int(code)).first()

        
            
# #         if product:
            

# #             return product, None
# #     except Exception as e:
# #         # Optional: log the exception
# #         print(f"Exact match error: {e}")

# #     # Weighted barcode
# #     if len(code) == config.total_bc_digits:
        
# #         try:
# #             trimmed = code[config.left_delete:len(code)-config.right_delete]
# #             item_code = trimmed[:config.item_bc]
# #             w = trimmed[config.item_bc:]
# #             kg = w[:config.kg]
# #             gr = w[config.kg:config.kg + config.grm]
# #             weight_total = Decimal(f'{kg}.{gr}')

# #             # Try to find the product by different barcode fields
# #             product = Inventory.objects.filter(
# #                 barcode=str(item_code)
# #             ).first() or Inventory.objects.filter(
# #                 manualbc__iexact=str(item_code)
# #             ).first() or Inventory.objects.filter(
# #                 barcode2__endswith=str(item_code)
# #             ).first() or Inventory.objects.filter(
# #                 inv_id = int(item_code)
# #                 ).first()
            
# #         except Exception as e:
# #             # Optional: log the exception
# #             print(f"Weighted barcode error: {e}")

# #     return product, weight_total


