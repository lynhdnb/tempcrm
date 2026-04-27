from django.contrib.auth.models import User

def impersonation_users(request):
    if request.user.is_authenticated and request.user.is_superuser:
        users = User.objects.filter(is_active=True).exclude(id=request.user.id)
        return {'impersonation_users': users}
    return {}
