
from django.shortcuts import render
from django.db import transaction

# from django.db.models import Q
from django.views.decorators.http import require_GET, require_POST
# 
# from django.core.paginator import Paginator, EmptyPage
from django.views.decorators.csrf import csrf_exempt


from decimal import Decimal
import json
from apps.purchase.models import Purchase
from apps.myglobal.services.helpers import get_next_voucher
from django.http import JsonResponse
from apps.purchase.services.purchase_helpers import json_to_invoice ,now_karachi , handle_inventory_valuation
# from apps.sale.services.
from django.forms.models import model_to_dict
from apps.purchase.services.purchase_calculations import calculate_landed_cost
from apps.myledger.models import Vchno ,Gledg
from apps.myledger.services.dto import GledgLineDTO
from apps.myledger.services.voucher_utills import create_gledg_entries

DEFAULT_LABOUR_PAYABLE_ACCOUNT = 231000123
DEFAULT_FREIGHT_PAYABLE_ACCOUNT =231000124
DEFAULT_UNLOAD_PAYABLE_ACCOUNT = 231000125
DEFAULT_MY_CASH_ACCOUNT = 110000001
DEFAULT_MY_BANK_ACCOUNT = 111000001
DEFAULT_MY_CASH_CLIENT_ACCOUNT = 112000001



@csrf_exempt
@require_POST
@transaction.atomic
def save_bill(request):
    user = request.user
    fields_will_update = {}
    system_fields = {}
    update=False
   
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    if isinstance(payload, dict):
        payload = [payload]
    elif not isinstance(payload, list):
        return JsonResponse({"success": False, "message": "Invalid payload format"})


    # print('palyod=============',payload)
    # print('payment mode' ,payload[0]['header_payment_mode'])
    for data in payload:
        items = data.get("items", [])
        
        if not items:
            return JsonResponse({"success": False, "message": "No items provided"})
    
        if data.get('bill_no'):
            old_bill_no = int(data.get('bill_no'))
            old_bill = Purchase.objects.filter(bill_no=old_bill_no, company = user.userprofile.company,branch = user.userprofile.branch)
            if not old_bill:
                return JsonResponse({"success": False, "message": "Bill not found"})
            old_item = old_bill.filter(is_header = True).first()
            fields_will_update = {
                'dateent': old_item.dateent,
                'date':old_item.date if not data.get('date') else data.get('date'),
                'header_edit_count': old_item.header_edit_count + 1,
                'user': old_item.user,
                "bill_no":old_bill_no,
            }
            update = True
            old_bill.delete()
            
        else:
            fields_will_update = {
                'dateent': now_karachi(),
                'date':now_karachi().date() if not data.get('date') else data.get('date'),
                'header_edit_count': 0,
                'user': user,
                "bill_no":get_next_voucher('PUR'),
            }   

        system_fields = {
            "user": user,
            "company": user.userprofile.company,
            "branch": user.userprofile.branch,
            "posterminal": user.userprofile.terminal,
        }

        landed_calcs = calculate_landed_cost(items, data)
        is_return = data.get('is_return',False)
        data.pop('local_id',None)
        data.pop('items',None)
        data.pop('date',None)
        data.pop('is_return',None)
        # Build Invoices
        invoices = []
        return_amount=0
        positive_amount=0

        for index, (item, landed) in enumerate(zip(items, landed_calcs)):
            is_first = (index == 0)
            return_amount += abs(item.get("row_net_total")) if int(item.get("row_net_total")) < 0 else 0
            positive_amount += item.get("row_net_total") if int(item.get("row_net_total")) > 0 else 0
            # (positive_amount >0 or data.get('header_freight_amount')>0 or data.get('header_labour_amount')>0 or data.get('header_unload_amount')>0 )
            if is_return and  positive_amount > 0 :
                return JsonResponse({"success": False, "message": f"Positive Qty not allowed {item.get('inv_id')}. For Return Switch To Purchase Return"})

            elif not is_return and (return_amount > 0 or (Decimal(data.get('header_freight_amount') or 0) < 0) or (Decimal(data.get('header_labour_amount') or 0) < 0) or (Decimal(data.get('header_unload_amount') or 0) < 0 )) :

                return JsonResponse({"success": False, "message": f"Negative Qty not allowed {item.get('inv_id')}. For Return Switch To Purchase Return"})
            
            # if not is_return:
            #     if int(item.get("row_net_total")) < 0:
            #         return JsonResponse({"success": False, "message": f"Negative Qty not allowed {item.get('inv_id')}. For Return Switch To Purchase Return"})
            # else:
            #     if int(item.get("row_net_total")) > 0:
            #         return JsonResponse({"success": False, "message": f"Positive Qty not allowed {item.get('inv_id')}. For Purchase Switch To Purchase"})
            
            invoices.append(json_to_invoice(
                item=item, 
                header_fields=data if is_first else {}, 
                fields_will_update=fields_will_update,
                system_fields=system_fields,
                is_header=is_first, 
                update=update,
                landed_calc=landed
            ))
            try:
                latest_purchase_vchno = int(Vchno.objects.filter(TYPE='PUR').only('VCHNO').first().VCHNO or 0)
                if latest_purchase_vchno == fields_will_update.get("bill_no"):
                    # print('qty', item.get('qty'))
                    # print('packqty', item.get('pack_qty'))
                    base_qty = int(item.get('qty')) * int(item.get('pack_qty'))
                    old_base_qty = item.get('row_old_total_base_qty') or 0
                    handle_inventory_valuation(item.get('inv_id'),base_qty,landed.get('row_total_cost'),called_from='PUR',old_base_qty=old_base_qty,update=update)
            except Exception as e:
                print('Error in save_bill', e)
        
        Purchase.objects.bulk_create(invoices)
        #create gledg entries        
        
        if Decimal(str(data.get('header_total_paid') or "0")) not in ( Decimal("0"),Decimal("1")):
            my_counter_account = DEFAULT_MY_CASH_ACCOUNT if not str(data.get('header_payment_mode')).startswith('111') else int(data.get('header_payment_mode'))
            # v_types = ['CP']
            # if return_amount !=0:   
            #     v_types.append('CR')
            # elif str(data.get('header_payment_mode')).startswith('111'):
            #     v_types = ["BR"]

            
            v_type = 'CP' if not str(data.get('header_payment_mode')).startswith('111') else 'BP'
            if is_return:
                v_type = 'CR' if not str(data.get('header_payment_mode')).startswith('111') else 'BR'
            # print('mycountacc',my_counter_account , 'v_type',v_type)
            lines = [
                GledgLineDTO(
                    accCode=int(data.get('header_acc_code') or 0),
                    head=data.get('head') or "",
                    notes= f"PUR# {fields_will_update.get('bill_no')}" if not is_return else f"PUR RETURN# {fields_will_update.get('bill_no')}",
                    receiptNo = 0,
                    chqNo = '0',
                    amount = Decimal(abs(Decimal(data.get('header_total_paid')))).quantize(Decimal("0.000")),
                    # amount = Decimal(positive_amount).quantize(Decimal("0.000")) if not is_return else Decimal(abs(return_amount)).quantize(Decimal("0.000")),
                    refAccCode = my_counter_account,
                    amtType = "DR" if not is_return else "CR",
                ),
            ]

            if Decimal(str(data.get("header_freight_amount") or "0")) != Decimal("0"):
                lines.append(
                    GledgLineDTO(
                        accCode=int(DEFAULT_FREIGHT_PAYABLE_ACCOUNT or 0) if not data.get('header_freight_acc_code') else int(data.get('header_freight_acc_code')),
                        head=data.get('head') or "",
                        notes= f"PUR# {fields_will_update.get('bill_no')}",
                        receiptNo = 0,
                        chqNo = '0',
                        amount = Decimal(abs(Decimal(data.get('header_freight_amount')))).quantize(Decimal("0.000")),
                        refAccCode = my_counter_account,
                        amtType = "DR" if Decimal(data.get('header_freight_amount')) > 0 else 'CR',
                    ),
                )

            if Decimal(str(data.get("header_labour_amount") or "0")) != Decimal("0"):
                lines.append(
                    GledgLineDTO(
                        accCode=int(DEFAULT_LABOUR_PAYABLE_ACCOUNT or 0) if not data.get('header_labour_acc_code') else int(data.get('header_labour_acc_code')),
                        head=data.get('head') or "",
                        notes= f"PUR# {fields_will_update.get('bill_no')}",
                        receiptNo = 0,
                        chqNo = '0',
                        amount = Decimal(abs(Decimal(data.get('header_labour_amount')))).quantize(Decimal("0.000")),
                        refAccCode = my_counter_account,
                        amtType = "DR" if Decimal(data.get('header_labour_amount')) > 0 else 'CR',
                    ),
                )

            if Decimal(str(data.get("header_unload_amount") or "0")) != Decimal("0"):
                lines.append(
                    GledgLineDTO(
                        accCode=int(DEFAULT_UNLOAD_PAYABLE_ACCOUNT or 0) if not data.get('header_unload_acc_code') else int(data.get('header_unload_acc_code')),
                        head=data.get('head') or "",
                        notes= f"PUR# {fields_will_update.get('bill_no')}",
                        receiptNo = 0,
                        chqNo = '0',
                        amount = Decimal(abs(Decimal(data.get('header_unload_amount')).quantize(Decimal("0.000")))),
                        refAccCode = my_counter_account,
                        amtType = "DR" if Decimal(data.get('header_unload_amount')) > 0 else 'CR',
                    ),
                )
            
            if update:
                old_gledg = Gledg.objects.filter(PUR_INV='P',INVOICE_ID=fields_will_update.get('bill_no')).only('VNO').first()
                if not old_gledg:
                    return JsonResponse({"success": False, "message": "Purchase invoice does not exists in ledger"})
            
            created,message = create_gledg_entries(
                request = request,
                lines=lines,
                date=fields_will_update.get('dateent'),
                v_type=v_type,
                remarks='',
                pur_inv='P',
                update=update,
                vno_to_update = old_gledg.VNO if update and old_gledg else 0,
                inv_id=fields_will_update.get('bill_no'),
                called_by_invoices = True,

            )
            if not created:
                raise Exception(f"Ledger creation failed: {message}")
    synced = []
    return JsonResponse({
        "success": True,"synced_bills": synced,"bill_no":fields_will_update.get('bill_no')
        
    })





def get_bill(request,bill_no):
    user = request.user
    if not bill_no:
        return JsonResponse({"success": False, "message": "Invalid bill_no"})

    try:
        bill = Purchase.objects.filter(bill_no=bill_no,company = user.userprofile.company,branch = user.userprofile.branch)
        # print('bill=============================',bill)
        if not bill:
            return JsonResponse({"success": False, "message": "Bill not found"})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})
    # header_row = bill.filter(is_header = True).first()
    # items = bill.filter(is_header = False)
    try:
        item_list = []
        for item in bill:
            if item.is_header:
                data_list = {
                "bill_no":item.bill_no,
                "branch":str(item.branch),
                "category":str(item.category),
                "company":str(item.company),
                "posterminal" :str(item.posterminal),
                "date":item.date,
                "dateedit":item.dateedit,
                "edit_by":item.edit_by,
                "header_bank_paid":item.header_bank_paid,
                "header_card_last4":item.header_card_last4,
                "header_cash_paid":item.header_cash_paid,
                "header_change_amount":item.header_change_amount,
                "header_delivery_charges":item.header_delivery_charges,
                "header_discount_amount":item.header_discount_amount,
                "header_discount_percent":item.header_discount_percent,
                "header_edit_count":item.header_edit_count,
                "header_gst_amount":item.header_gst_amount,
                "header_gst_percent":item.header_gst_percent,
                "header_item_total":item.header_item_total,
                "header_msc_charges":item.header_msc_charges,
                "header_net_total":item.header_net_total,
                "header_payment_mode":item.header_payment_mode,
                "header_remarks":item.header_remarks,
                'date':item.date.strftime('%m-%d-%Y') if item.date else None,
                'header_supl_inv_no':item.header_supl_inv_no,
                'header_supl_inv_date':item.header_supl_inv_date.strftime('%m-%d-%Y') if item.header_supl_inv_date else None,
                'header_our_ref':item.header_our_ref,
                'header_our_ref_date':item.header_our_ref_date.strftime('%m-%d-%Y') if item.header_our_ref_date else None,
                'header_delivery_person':item.header_delivery_person,
                'header_freight_amount':item.header_freight_amount,
                'header_labour_amount':item.header_labour_amount,
                'header_unload_amount':item.header_unload_amount,
                "header_total_items":item.header_total_items,
                "header_total_paid" :item.header_total_paid,
                "user" :str(item.user),
                "salesman" :item.salesman,
                "is_header":item.is_header,
                "header_acc_code":item.header_acc_code,
            }
            item_list.append({
                "inv_id":item.inv_id,
                "pack_qty" :item.pack_qty,
                "packing_mode" :item.packing_mode,
                "prod_name" :item.prod_name,
                "qty" :item.qty,
                "rate" :item.rate,
                "row_discount_amount" :item.row_discount_amount,
                "row_discount_percent" :item.row_discount_percent,
                "row_net_total" :item.row_net_total,
                "row_notes" :item.row_notes,
                "uom" :item.uom,
                'row_expiry_dt':item.row_expiry_dt.strftime('%Y-%m-%d') if item.row_expiry_dt else None,
                'row_batch_no':item.row_batch_no if item.row_batch_no else None,

                })
        data_list['items']=item_list
        # print('data_list======================',item_list)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})
    # print('dtataa===================',data_list)
    return JsonResponse({"success": True,"data": data_list,"message":'Successfully Loaded!'})



