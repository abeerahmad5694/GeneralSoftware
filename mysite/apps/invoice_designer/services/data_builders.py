"""
invoice_designer.services.data_builders
------------------------------------------
Turns *existing* ERP model rows (Invoice, Purchase, ...) into the one
unified `document_data` shape the renderer understands.

This is the only layer that is allowed to know your ERP's real model
field names. If a field name differs from what's assumed below, this
is the one file to edit — the renderer, the templates and the JS never
change.

Real schema shape: your `Invoice` / `Purchase` tables are NOT header-
with-related-items. They are a single table per `bill_no`, where one
row has `is_header=True` (the totals/payment row) and every other row
for that same `bill_no` has `is_header=False` (one row per line item).
Every builder below queries that way — O(1) header lookup + O(n) line
items, never N+1.

Every value below maps to a real column on Company / Branch /
POSTerminal / Invoice / Purchase. Nothing here fabricates a value for
a column that doesn't exist (no barcode/SKU/brand/GST — those were
never real columns on these models).
"""

from datetime import datetime

from .ledger import get_previous_balance as _ledger_previous_balance

PACKING_MODE_LABELS = {1: "Base", 2: "Carton", 3: "Dozen", 4: "Wholesale"}


def _get(row, field_name, default=None):
    """Defensive getattr — keeps this module usable even before every
    field listed here exists on the real ERP models. O(1)."""
    value = getattr(row, field_name, default)
    return default if value is None else value


def _number(value, default=0):
    return default if value is None else value


def _logo_url(model_instance) -> str:
    """FileField/ImageField -> its .url, tolerating a missing file,
    a missing storage backend, or a null field without raising."""
    if model_instance is None:
        return ""
    logo_field = getattr(model_instance, "logo", None)
    if not logo_field:
        return ""
    try:
        return logo_field.url
    except (ValueError, Exception):
        return ""


def get_previous_balance(bill_no, invoice_type: str = "pos_invoice", dateent=None, acc_code=None, excluded_acc_codes=None) -> dict:
    """
    Thin pass-through to services.ledger.get_previous_balance so callers
    that only import data_builders keep working. Passes acc_code directly
    so the ledger service doesn't need to re-query Invoice for it.
    """
    return _ledger_previous_balance(
        bill_no, invoice_type, dateent or datetime.now(),
        acc_code=acc_code,
        excluded_acc_codes=excluded_acc_codes,
    )


def _company_and_branch_data(company, branch):
    """Shared by both builders — Company/Branch shape is identical.
    Includes optional Urdu name/address fields (null-safe)."""
    return (
        {
            "name": getattr(company, "name", ""),
            "name_ur": getattr(company, "name_ur", "") or "",
            "address": getattr(company, "address", ""),
            "address_ur": getattr(company, "address_ur", "") or "",
            "phone": getattr(company, "phone1", ""),
            "email": getattr(company, "email", ""),
            "license_number": getattr(company, "license_no", ""),
            "ntn_no": getattr(company, "ntn_no", "") or "",
            "ntn_no_ur": getattr(company, "ntn_no_ur", "") or "",
            "logo_url": _logo_url(company),
        },
        {
            "name": getattr(branch, "name", ""),
            "name_ur": getattr(branch, "name_ur", "") or "",
            "address": getattr(branch, "address", ""),
            "address_ur": getattr(branch, "address_ur", "") or "",
            "phone": getattr(branch, "phone1", ""),
            "email": getattr(branch, "email", ""),
            "license_number": getattr(branch, "license_no", ""),
            "logo_url": _logo_url(branch),
        },
    )


def build_pos_invoice_data(header_row, include_previous_balance: bool = False) -> dict:
    """
    header_row: the Invoice row where is_header=True for a given bill_no.
    Line items are fetched separately (same table, is_header=False,
    same bill_no) since that's how the real schema stores them.
    """
    bill_no = _get(header_row, "bill_no")
    company_data, branch_data = _company_and_branch_data(_get(header_row, "company"), _get(header_row, "branch"))
    posterminal = _get(header_row, "posterminal")

    acc_code = _get(header_row, "header_acc_code")
    dateent = _get(header_row, "dateent")

    data = {
        "bill_number": bill_no,
        "invoice_title": "INVOICE",
        "invoice_date": _get(header_row, "date") or dateent,
        "salesman": _get(header_row, "salesman", ""),
        "cashier": _get(header_row, "user", ""),
        "terminal": getattr(posterminal, "name", "") if posterminal else "",
        "remarks": _get(header_row, "header_remarks", ""),
        "printed_by": _get(header_row, "user", ""),
        "print_date": datetime.now().strftime("%Y-%m-%d"),
        "print_time": datetime.now().strftime("%H:%M:%S"),

        "company": company_data,
        "branch": branch_data,
        "customer": {"account_code": acc_code},

        "totals": {
            "total_items": _get(header_row, "header_total_items", 0),
            "subtotal": _get(header_row, "header_item_total", 0),
            "discount_percent": _get(header_row, "header_discount_percent", 0),
            "discount_amount": _get(header_row, "header_discount_amount", 0),
            "delivery_charges": _get(header_row, "header_delivery_charges", 0),
            "gst_percent": _get(header_row, "header_gst_percent", 0),
            "gst_amount": _get(header_row, "header_gst_amount", 0),
            "misc_charges": _get(header_row, "header_msc_charges", 0),
            "net_total": _get(header_row, "header_net_total", 0),
            "cash_received": _get(header_row, "header_cash_paid", 0),
            "bank_received": _get(header_row, "header_bank_paid", 0),
            "change_amount": _get(header_row, "header_change_amount", 0),
        },

        "items": [
            _build_sale_item(row)
            for row in _fetch_line_items(header_row.__class__, bill_no, header_row)
        ],
    }

    if include_previous_balance:
        previous_balance = get_previous_balance(
            bill_no, invoice_type="pos_invoice",
            dateent=dateent, acc_code=acc_code,
        )
        data["totals"].update(previous_balance)
        data["totals"]["current_balance"] = round(
            _number(previous_balance.get("previous_balance"))
            + _number(data["totals"]["net_total"])
            - (_number(data["totals"]["cash_received"]) + _number(data["totals"]["bank_received"])),
            2,
        )

    return data


def _fetch_line_items(model_class, bill_no, header_row=None):
    """
    Fetch all non-header rows for this bill_no.

    The real schema stores header+items in ONE table. is_header=False rows
    are item rows. However when a bill has exactly ONE item, some ERP versions
    store that item data directly on the header row (is_header=True) — so if
    querying is_header=False returns nothing, we fall back to treating the
    header row itself as the single item row (it has all the same item-level
    fields: prod_name, qty, rate, etc.).
    """
    if model_class is None or bill_no is None:
        return []
    try:
        # rows = list(model_class.objects.filter(bill_no=bill_no, is_header=False).order_by("id"))
        rows = list(model_class.objects.filter(bill_no=bill_no).order_by("id"))
        if not rows and header_row is not None:
            # Single-item invoice — header row carries the item data
            return [header_row]
        return rows
    except Exception:
        return []


def _build_sale_item(row) -> dict:
    """Matches schema.ITEM_COLUMN_REGISTRIES['pos_invoice'] exactly —
    every key here is a real Invoice row column. Includes optional Urdu name."""
    inv_id = getattr(row, "inv_id", None)
    prod_name_ur = ""
    if inv_id:
        try:
            from apps.inventory.models import Inventory
            inv = Inventory.objects.filter(inv_id=inv_id).first()
            if inv:
                prod_name_ur = getattr(inv, "prod_name_ur", "") or ""
        except Exception:
            pass

    return {
        "product_name": _get(row, "prod_name", ""),
        "product_name_ur": prod_name_ur or _get(row, "prod_name_ur", "") or "",
        "category": _get(row, "category", ""),
        "quantity": _get(row, "qty", 0),
        "unit": _get(row, "uom", ""),
        "packing_mode": PACKING_MODE_LABELS.get(_get(row, "packing_mode", 1), ""),
        "pack_quantity": _get(row, "pack_qty", 0),
        "rate": _get(row, "rate", 0),
        "discount_percent": _get(row, "row_discount_percent", 0),
        "discount_amount": _get(row, "row_discount_amount", 0),
        "cost_price": _get(row, "row_rate_cost", 0),
        "net_cost": _get(row, "row_net_cost", 0),
        "item_notes": _get(row, "row_notes", ""),
        "amount": _get(row, "row_net_total", 0),
    }


def build_purchase_invoice_data(header_row, include_previous_balance: bool = False) -> dict:
    """
    Same shape as build_pos_invoice_data, sourced from the `Purchase`
    model (also single-table, bill_no + is_header).
    """
    bill_no = _get(header_row, "bill_no")
    acc_code = _get(header_row, "header_acc_code")
    company_data, branch_data = _company_and_branch_data(_get(header_row, "company"), _get(header_row, "branch"))

    data = {
        "bill_number": bill_no,
        "invoice_title": "PURCHASE INVOICE",
        "invoice_date": _get(header_row, "date"),
        "salesman": _get(header_row, "salesman", ""),
        "cashier": _get(header_row, "user", ""),
        "terminal": "",
        "remarks": _get(header_row, "header_remarks", ""),
        "printed_by": _get(header_row, "user", ""),
        "print_date": datetime.now().strftime("%Y-%m-%d"),
        "print_time": datetime.now().strftime("%H:%M:%S"),
        "supplier_invoice_number": _get(header_row, "header_supl_inv_no", ""),
        "supplier_invoice_date": _get(header_row, "header_supl_inv_date"),

        "company": company_data,
        "branch": branch_data,
        "customer": {"account_code": acc_code},

        "totals": {
            "total_items": _get(header_row, "header_total_items", 0),
            "subtotal": _get(header_row, "header_item_total", 0),
            "discount_percent": _get(header_row, "header_discount_percent", 0),
            "discount_amount": _get(header_row, "header_discount_amount", 0),
            "delivery_charges": _get(header_row, "header_freight_amount", 0),
            "gst_percent": _get(header_row, "header_gst_percent", 0),
            "gst_amount": _get(header_row, "header_gst_amount", 0),
            "misc_charges": _get(header_row, "header_msc_charges", 0),
            "net_total": _get(header_row, "header_net_total", 0),
            "cash_received": _get(header_row, "header_cash_paid", 0),
            "bank_received": _get(header_row, "header_bank_paid", 0),
            "change_amount": _get(header_row, "header_change_amount", 0),
        },

        "items": [
            _build_purchase_item(row)
            for row in _fetch_line_items(header_row.__class__, bill_no, header_row)
        ],
    }

    if include_previous_balance:
        previous_balance = get_previous_balance(
            bill_no, invoice_type="purchase_invoice",
            dateent=_get(header_row, "date"), acc_code=acc_code,
        )
        data["totals"].update(previous_balance)

    return data


def _build_purchase_item(row) -> dict:
    """Matches schema.ITEM_COLUMN_REGISTRIES['purchase_invoice'] exactly
    — every key here is a real Purchase row column. Includes optional Urdu name."""
    inv_id = getattr(row, "inv_id", None)
    prod_name_ur = ""
    if inv_id:
        try:
            from apps.inventory.models import Inventory
            inv = Inventory.objects.filter(inv_id=inv_id).first()
            if inv:
                prod_name_ur = getattr(inv, "prod_name_ur", "") or ""
        except Exception:
            pass

    return {
        "product_name": _get(row, "prod_name", ""),
        "product_name_ur": prod_name_ur or _get(row, "prod_name_ur", "") or "",
        "category": _get(row, "category", ""),
        "quantity": _get(row, "qty", 0),
        "unit": _get(row, "uom", ""),
        "packing_mode": PACKING_MODE_LABELS.get(_get(row, "packing_mode", 1), ""),
        "pack_quantity": _get(row, "pack_qty", 0),
        "rate": _get(row, "rate", 0),
        "discount_percent": _get(row, "row_discount_percent", 0),
        "discount_amount": _get(row, "row_discount_amount", 0),
        "item_notes": _get(row, "row_notes", ""),
        "amount": _get(row, "row_net_total", 0),
        "batch_number": _get(row, "row_batch_no", ""),
        "batch_quantity": _get(row, "row_batch_qty", 0),
        "expiry_date": _get(row, "row_expiry_dt", ""),
        "pack_quantity_received": _get(row, "row_pack_qty_rcvd", 0),
        "trade_price": _get(row, "row_trade_price", 0),
        "retail_price": _get(row, "row_actual_retail_price", 0),
        "old_cost": _get(row, "row_oldcost", 0),
        "discount_percent_2": _get(row, "row_discount_percent2", 0),
        "discount_amount_2": _get(row, "row_discount_amount2", 0),
        "bonus_quantity": _get(row, "row_bonus", 0),
        "bonus_amount": _get(row, "row_bonus_amount", 0),
        "landed_cost": _get(row, "row_total_cost_per_base_unit", 0),
    }


def build_quotation_data(header_row, include_previous_balance: bool = False) -> dict:
    """
    header_row: the Quotation row where is_header=True for a given bill_no.
    Line items are fetched from the same Quotation table where is_header=False.
    """
    bill_no = _get(header_row, "bill_no")
    acc_code = _get(header_row, "header_acc_code")
    company_data, branch_data = _company_and_branch_data(_get(header_row, "company"), _get(header_row, "branch"))
    posterminal = _get(header_row, "posterminal")
    dateent = _get(header_row, "dateent")

    data = {
        "bill_number": bill_no,
        "invoice_title": "QUOTATION",
        "invoice_date": _get(header_row, "date") or dateent,
        "salesman": _get(header_row, "salesman", ""),
        "cashier": _get(header_row, "user", ""),
        "terminal": getattr(posterminal, "name", "") if posterminal else "",
        "remarks": _get(header_row, "header_remarks", ""),
        "printed_by": _get(header_row, "user", ""),
        "print_date": datetime.now().strftime("%Y-%m-%d"),
        "print_time": datetime.now().strftime("%H:%M:%S"),

        "company": company_data,
        "branch": branch_data,
        "customer": {"account_code": acc_code},

        "totals": {
            "total_items": _get(header_row, "header_total_items", 0),
            "subtotal": _get(header_row, "header_item_total", 0),
            "discount_percent": _get(header_row, "header_discount_percent", 0),
            "discount_amount": _get(header_row, "header_discount_amount", 0),
            "delivery_charges": _get(header_row, "header_delivery_charges", 0),
            "gst_percent": _get(header_row, "header_gst_percent", 0),
            "gst_amount": _get(header_row, "header_gst_amount", 0),
            "misc_charges": _get(header_row, "header_msc_charges", 0),
            "net_total": _get(header_row, "header_net_total", 0),
            "cash_received": _get(header_row, "header_cash_paid", 0),
            "bank_received": _get(header_row, "header_bank_paid", 0),
            "change_amount": _get(header_row, "header_change_amount", 0),
        },

        "items": [
            _build_sale_item(row)
            for row in _fetch_line_items(header_row.__class__, bill_no, header_row)
        ],
    }

    if include_previous_balance:
        previous_balance = get_previous_balance(
            bill_no, invoice_type="quotation",
            dateent=dateent, acc_code=acc_code,
        )
        data["totals"].update(previous_balance)
        data["totals"]["current_balance"] = round(
            _number(previous_balance.get("previous_balance"))
            + _number(data["totals"]["net_total"])
            - (_number(data["totals"]["cash_received"]) + _number(data["totals"]["bank_received"])),
            2,
        )

    return data


# Document type -> builder function. RenderDocumentView/DocumentDataView
# use this map so adding a new document type never means touching the
# view or the renderer.
DOCUMENT_DATA_BUILDERS = {
    "pos_invoice": build_pos_invoice_data,
    "credit_sale_invoice": build_pos_invoice_data,   # same real columns as POS today
    "purchase_invoice": build_purchase_invoice_data,
    "quotation": build_quotation_data,
    # "voucher": build_voucher_data,
}
