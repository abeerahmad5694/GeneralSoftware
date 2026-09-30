from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, Count, F, Q
from django.contrib.auth.decorators import login_required
import datetime
from decimal import Decimal

from apps.sale.models import Invoice
from apps.purchase.models import Purchase
from apps.inventory.models import Inventory
from apps.myledger.models import Gledg
from apps.myaccounts.models import Accounts

# ══════════════════════════════════════════════════════════════════════════
# GLOBAL CONFIGURATION FOR DASHBOARD CALCULATIONS (Customizable)
# ══════════════════════════════════════════════════════════════════════════
# Top-level Expense Root Account Code in Chart of Accounts (e.g. 3 for EXPENSES)
EXPENSE_ACCOUNT_CODE = 3

# Level of Expense Root in Chart of Accounts
EXPENSE_ACCOUNT_LEVEL = 1

# Specific Voucher Types considered for Expense Calculations
# Leave as list of types (e.g. ['CP', 'BP', 'JV']) or None to consider all types
EXPENSE_V_TYPES = ['CP', 'BP', 'JV', 'CR', 'BR']


from apps.myledger.services.helpers import get_user_perms
from django.shortcuts import render, redirect

@login_required
def dashboard(request):
    can_view, message = get_user_perms(request, "view_dashboard")
    if not can_view:
        return redirect('sale:main_sale')
    return render(request, 'dashboard/dashboard.html')


@login_required
def dashboard_stats(request):
    can_view, message = get_user_perms(request, "view_dashboard")
    if not can_view:
        return JsonResponse({'success': False, 'message': message}, status=403)
    """
    All dashboard KPIs in a single endpoint.
    Optimized single-pass aggregations matching Daybook & General Ledger logic.
    """
    today = datetime.date.today()
    this_month_start = today.replace(day=1)

    def _d(val):
        return float(val or 0)

    # ── 1. Sales: today + this month ───────────────────────────────────────
    sale_headers = Invoice.objects.filter(is_header=True)

    sale_today = sale_headers.filter(date=today).aggregate(
        total=Sum('header_net_total'),
        bills=Count('bill_no', distinct=True),
        cash=Sum('header_cash_paid'),
        bank=Sum('header_bank_paid'),
    )
    sale_month = sale_headers.filter(date__gte=this_month_start).aggregate(
        total=Sum('header_net_total'),
        bills=Count('bill_no', distinct=True),
    )

    # ── 2. Purchases: today + this month ──────────────────────────────────
    pur_headers = Purchase.objects.filter(is_header=True)

    pur_today = pur_headers.filter(date=today).aggregate(
        total=Sum('header_net_total'),
        bills=Count('bill_no', distinct=True),
    )
    pur_month = pur_headers.filter(date__gte=this_month_start).aggregate(
        total=Sum('header_net_total'),
        bills=Count('bill_no', distinct=True),
    )

    # ── 3. Total Expense Calculation from Gledg (using Global Variables) ───
    # Identify expense accounts from Accounts hierarchy
    expense_accounts_qs = Accounts.objects.filter(
        Q(ACC_CODE__startswith=str(EXPENSE_ACCOUNT_CODE)) |
        Q(CLASS_FIELD__iexact='Expense') |
        Q(TYPE__iexact='Expense')
    )
    if EXPENSE_ACCOUNT_LEVEL:
        expense_accounts_qs = expense_accounts_qs.filter(LEVEL__gte=EXPENSE_ACCOUNT_LEVEL)

    expense_acc_codes = list(expense_accounts_qs.values_list('ACC_CODE', flat=True))

    gledg_exp_today = Gledg.objects.filter(ACC_CODE__in=expense_acc_codes, DATE=today)
    gledg_exp_month = Gledg.objects.filter(ACC_CODE__in=expense_acc_codes, DATE__gte=this_month_start)

    if EXPENSE_V_TYPES:
        gledg_exp_today = gledg_exp_today.filter(V_TYPE__in=EXPENSE_V_TYPES)
        gledg_exp_month = gledg_exp_month.filter(V_TYPE__in=EXPENSE_V_TYPES)

    exp_today_agg = gledg_exp_today.aggregate(
        debit=Sum('AMOUNT', filter=Q(AMT_TYPE='DR')),
        credit=Sum('AMOUNT', filter=Q(AMT_TYPE='CR')),
        count=Count('GLEDG_ID')
    )
    exp_month_agg = gledg_exp_month.aggregate(
        debit=Sum('AMOUNT', filter=Q(AMT_TYPE='DR')),
        credit=Sum('AMOUNT', filter=Q(AMT_TYPE='CR')),
        count=Count('GLEDG_ID')
    )

    total_expense_today = _d((exp_today_agg['debit'] or Decimal('0.00')) - (exp_today_agg['credit'] or Decimal('0.00')))
    total_expense_month = _d((exp_month_agg['debit'] or Decimal('0.00')) - (exp_month_agg['credit'] or Decimal('0.00')))

    # ── 4. Cash & Bank Activity from Gledg (Daybook / Ledger logic) ────────
    gledg_today = Gledg.objects.filter(DATE=today)

    def calc_voucher_metric(vtype):
        # In daybook: row['v_type'] == vtype and row['credit'] > 0
        res = gledg_today.filter(V_TYPE=vtype, AMT_TYPE='CR').aggregate(total=Sum('AMOUNT'), count=Count('GLEDG_ID'))
        total = res['total']
        if total is None:
            # Fallback if single leg or DR stored
            res = gledg_today.filter(V_TYPE=vtype).aggregate(total=Sum('AMOUNT'), count=Count('GLEDG_ID'))
            total = res['total']
        return _d(total), res['count'] or 0

    cash_received_today, cr_count = calc_voucher_metric('CR')
    cash_paid_today, cp_count     = calc_voucher_metric('CP')
    bank_received_today, br_count = calc_voucher_metric('BR')
    bank_paid_today, bp_count     = calc_voucher_metric('BP')

    # ── 5. Last 7 Days: Sales vs Purchases Chart ──────────────────────────
    seven_days_ago = today - datetime.timedelta(days=6)
    daily_sales = (
        sale_headers
        .filter(date__gte=seven_days_ago)
        .values('date')
        .annotate(total=Sum('header_net_total'), bills=Count('bill_no', distinct=True))
        .order_by('date')
    )
    daily_purchases = (
        pur_headers
        .filter(date__gte=seven_days_ago)
        .values('date')
        .annotate(total=Sum('header_net_total'))
        .order_by('date')
    )

    pur_map = {row['date']: _d(row['total']) for row in daily_purchases}
    sale_map = {row['date']: _d(row['total']) for row in daily_sales}

    chart_labels = []
    chart_sales = []
    chart_purchases = []
    for i in range(7):
        d = seven_days_ago + datetime.timedelta(days=i)
        chart_labels.append(d.strftime('%d %b'))
        chart_sales.append(sale_map.get(d, 0))
        chart_purchases.append(pur_map.get(d, 0))

    # ── 6. Top 8 Products Today (by revenue) ──────────────────────────────
    top_products = (
        Invoice.objects
        .filter(is_header=False, date=today)
        .values('prod_name', 'inv_id')
        .annotate(
            revenue=Sum('row_net_total'),
            qty=Sum('qty'),
        )
        .order_by('-revenue')[:8]
    )

    # ── 7. Inventory Low Stock Alerts ─────────────────────────────────────
    low_stock = (
        Inventory.objects
        .filter(active=True, reorder__isnull=False)
        .filter(Q(bal_qty__lte=F('reorder')) | Q(bal_qty__lte=0))
        .values('inv_id', 'prod_name', 'bal_qty', 'reorder', 'base_price')
        .order_by('bal_qty')[:10]
    )

    # ── 8. Recent Vouchers & Transactions Today (from Gledg) ───────────────
    recent_gledg = (
        gledg_today
        .filter(V_TYPE__in=['CR', 'CP', 'BR', 'BP', 'JV'])
        .values('GLEDG_ID', 'V_TYPE', 'VNO', 'ACC_CODE', 'DESCRIPTION', 'AMOUNT', 'AMT_TYPE', 'DATEENT')
        .order_by('-DATEENT', '-GLEDG_ID')[:5]
    )

    return JsonResponse({
        'today': today.strftime('%d %b %Y'),
        'kpi': {
            'sale_today':         _d(sale_today['total']),
            'sale_bills_today':   sale_today['bills'] or 0,
            'sale_month':         _d(sale_month['total']),
            'sale_bills_month':   sale_month['bills'] or 0,
            'pur_today':          _d(pur_today['total']),
            'pur_bills_today':    pur_today['bills'] or 0,
            'pur_month':          _d(pur_month['total']),
            'pur_bills_month':    pur_month['bills'] or 0,
            'expense_today':      total_expense_today,
            'expense_month':      total_expense_month,
            'expense_count_today': exp_today_agg['count'] or 0,
            'low_stock_count':    len(list(low_stock)),
        },
        'vouchers_today': {
            'cash_received': cash_received_today,
            'cash_paid':     cash_paid_today,
            'bank_received': bank_received_today,
            'bank_paid':     bank_paid_today,
            'cr_count':      cr_count,
            'cp_count':      cp_count,
            'br_count':      br_count,
            'bp_count':      bp_count,
        },
        'chart': {
            'labels':    chart_labels,
            'sales':     chart_sales,
            'purchases': chart_purchases,
        },
        'top_products': [
            {
                'name':    r['prod_name'] or '—',
                'inv_id':  r['inv_id'],
                'revenue': _d(r['revenue']),
                'qty':     _d(r['qty']),
            }
            for r in top_products
        ],
        'low_stock': [
            {
                'inv_id':   r['inv_id'],
                'name':     r['prod_name'] or '—',
                'bal_qty':  r['bal_qty'] or 0,
                'reorder':  r['reorder'] or 0,
                'price':    _d(r['base_price']),
            }
            for r in low_stock
        ],
        'recent_vouchers': [
            {
                'id':       r['GLEDG_ID'],
                'v_type':   (r['V_TYPE'] or '').strip().upper(),
                'vno':      r['VNO'] or 0,
                'acc_code': r['ACC_CODE'] or 0,
                'desc':     (r['DESCRIPTION'] or '—').strip(),
                'amount':   _d(r['AMOUNT']),
                'amt_type': (r['AMT_TYPE'] or '').strip().upper(),
                'time':     r['DATEENT'].strftime('%H:%M') if r['DATEENT'] else '—',
            }
            for r in recent_gledg
        ],
    })
