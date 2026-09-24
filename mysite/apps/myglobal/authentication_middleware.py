from django.shortcuts import redirect, render
from django.urls import reverse
from datetime import datetime , timezone
from django.conf import settings
from django.utils.timezone import now
class loginrequiredmiddleware:
    def __init__(self,get_response):
        self.get_response = get_response
    
    
    def __call__(self,request):
        if request.path.startswith('/admin'):
            return self.get_response(request)
        if not request.user.is_authenticated and request.path not in (settings.LOGIN_URL,settings.LOGOUT_URL):
            return redirect(settings.LOGIN_URL)

        response = self.get_response(request)
        return response



class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')

            if last_activity:
                last_activity_time = now().timestamp()
                if now().timestamp() - last_activity > 1600:
                    from django.contrib.auth import logout
                    logout(request)
                    return redirect(reverse('login'))

            request.session['last_activity'] = now().timestamp()

        return self.get_response(request)