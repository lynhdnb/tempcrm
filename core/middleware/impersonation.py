from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin

User = get_user_model()

class ImpersonationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not hasattr(request, 'user'):
            return

        impersonated_user_id = request.session.get('impersonated_user_id')
        if impersonated_user_id and request.user.is_superuser:
            try:
                impersonated_user = User.objects.select_related('profile').get(id=impersonated_user_id)
                # Очищаем кэш профиля, если был
                if hasattr(request.user, '_profile_cache'):
                    delattr(request.user, '_profile_cache')
                request.impersonator = request.user
                request.user = impersonated_user
            except User.DoesNotExist:
                pass
