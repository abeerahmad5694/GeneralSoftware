from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import transaction
from apps.inventory.forms.inventory import InventoryForm
from apps.inventory.models import Inventory


from apps.myledger.services.helpers import get_user_perms
from apps.users.api.license import validate_license

@validate_license
@transaction.atomic
def inventory(request):
    can_view, message = get_user_perms(request, 'view_inventory')
    if not can_view:
        return redirect('page_not_found')
    
    # Inventory.objects.all().delete()
    company = request.user.userprofile.company
    branch = request.user.userprofile.branch
    form = InventoryForm()
    if request.method=='POST':
        try:
            with transaction.atomic():
                old_inv_id = request.POST.get('inv_id')
                if old_inv_id:
                    try:
                        old_inv_obj = Inventory.objects.get(inv_id=old_inv_id)
                        form = InventoryForm(request.POST, instance=old_inv_obj)
                    except Inventory.DoesNotExist:
                        form = InventoryForm(request.POST)
                else:
                    form = InventoryForm(request.POST)
                if form.is_valid():
                    inv_instance = form.save(commit=False)
                    inv_instance.company = company
                    inv_instance.branch = branch
                    inv_instance.save()
                    return redirect('inventory')
                else:
                    print(form.errors)
                    return redirect('inventory')
        except Exception as e:
            print(f"Error saving inventory item: {e}")
            return redirect('inventory')
    some_inventory_products = Inventory.objects.filter(company =company, branch = branch).values('inv_id','prod_name').order_by('-inv_id')[:15] 
    context = {
        'form': form,
        'company_id': company.id,
        'branch_id': branch.id,
        'some_inventory_products':some_inventory_products
    }
    return render(request, 'inventory/inventory.html', context)




def get_item_by_id(request , inv_id):
    inventory = Inventory.objects.filter(company = request.user.userprofile.company, branch = request.user.userprofile.branch, inv_id=inv_id).first()
    if not inventory:
        return JsonResponse({'success':False, 'message':'Item not found. Pleae Refresh Your Offline Inventory!'})

    form = InventoryForm(instance=inventory)
    data = {}
    for field in form:
        # print(field.name)
        data[field.name] = field.value()
        if field.name == 'date' and field.value() is not None:
            data[field.name] = field.value().strftime('%Y-%m-%d')
        elif field.name == 'expiry_date' and field.value() is not None:
            data[field.name] = field.value().strftime('%Y-%m-%d')
        else:
            data[field.name] = field.value()

    data['inv_id'] = inventory.inv_id
    return JsonResponse({'success':True, 'data':data})