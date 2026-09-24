from apps.myledger.services.helpers import get_user_perms
from django.shortcuts import redirect

from django.contrib.auth.models import User, Group
from django.contrib import messages
from apps.users.models import Role, Permission, UserProfile
from apps.configuration.models import Company, Branch
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

@login_required

def permissions(request):
    can_view, message = get_user_perms(request, 'manage_users')
    if not can_view:
        return redirect('page_not_found')

    company = Company.objects.first()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_role':
            name = request.POST.get('role_name')
            if name and company:
                role, created = Role.objects.get_or_create(name=name, company=company)
                if created:
                    messages.success(request, f'Role "{name}" created successfully.')
                else:
                    messages.error(request, f'Role "{name}" already exists.')
                return redirect(f"{request.path}?role_id={role.id}")
                
        elif action == 'delete_role':
            role_id = request.POST.get('role_id')
            role = get_object_or_404(Role, id=role_id, company=company)
            role.delete()
            messages.success(request, 'Role deleted successfully.')
            return redirect('permissions')
            
        elif action == 'update_permissions':
            role_id = request.POST.get('role_id')
            role = get_object_or_404(Role, id=role_id, company=company)
            perms_codes = request.POST.getlist('permissions')
            perms = Permission.objects.filter(code__in=perms_codes)
            role.permissions.set(perms)
            messages.success(request, 'Permissions updated successfully.')
            return redirect(f"{request.path}?role_id={role.id}")

    roles = Role.objects.filter(company=company) if company else []
    active_role_id = request.GET.get('role_id')
    
    if active_role_id and company:
        try:
            active_role = Role.objects.get(id=active_role_id, company=company)
        except Role.DoesNotExist:
            active_role = roles.first() if roles else None
    else:
        active_role = roles.first() if roles else None

    # Group permissions by module
    all_perms = Permission.objects.all().order_by('module', 'name')
   
    
    modules = {}
    for p in all_perms:
        modules.setdefault(p.module, []).append(p)
    print(f"DEBUG: Modules count: {len(modules)}")

    active_perms = []
    if active_role:
        active_perms = list(active_role.permissions.values_list('code', flat=True))

    return render(request, 'users/permissions.html', {
        'roles': roles,
        'active_role': active_role,
        'modules': modules,
        'active_perms': active_perms,
    })

