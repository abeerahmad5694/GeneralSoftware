def user_perms(request):
    if request.user.is_authenticated:
        if not hasattr(request, '_user_perm_codes'):
            request._user_perm_codes = set(request.user.userprofile.get_permissions().values_list('code', flat=True))
        return {'user_perm_codes': request._user_perm_codes}
    return {}
