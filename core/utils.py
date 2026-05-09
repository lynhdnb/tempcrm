"""
Утилиты для унифицированных ответов API (аналог AlfaCRM)
"""

from rest_framework.response import Response
from rest_framework import status


class AlfaStyleResponse:
    """
    Унифицированный формат ответов API (аналог AlfaCRM)
    
    Примеры:
    
    # Успешный ответ для create/update
    AlfaStyleResponse.success(data, message="Успешно")
    
    # Успешный ответ для index (с пейджинацией)
    AlfaStyleResponse.index(items, total, page=0, count=0)
    
    # Ответ с ошибкой
    AlfaStyleResponse.error(["Ошибка 1", "Ошибка 2"], message="Не удалось сохранить")
    """
    
    @staticmethod
    def success(data=None, message="", extra=None):
        """
        Успешный ответ для create/update/delete
        
        Пример:
        {
            "success": true,
            "errors": [],
            "message": "Успешно",
            "model": {...}
        }
        """
        response = {
            "success": True,
            "errors": [],
            "model": data,
        }
        
        if message:
            response["message"] = message
        
        if extra:
            response.update(extra)
        
        return Response(response, status=status.HTTP_200_OK)
    
    @staticmethod
    def success_created(data=None, message="Создано"):
        """Успешный ответ при создании (201)"""
        return Response({
            "success": True,
            "errors": [],
            "message": message,
            "model": data,
        }, status=status.HTTP_201_CREATED)
    
    @staticmethod
    def success_deleted(message="Удалено"):
        """Успешный ответ при удалении"""
        return Response({
            "success": True,
            "errors": [],
            "message": message,
        }, status=status.HTTP_200_OK)
    
    @staticmethod
    def index(items, total, page=0, count=None, extra=None):
        """
        Успешный ответ для index (список с пейджинацией)
        
        Пример:
        {
            "total": 50,
            "count": 20,
            "page": 0,
            "items": [...]
        }
        """
        response = {
            "total": total,
            "count": count if count else len(items),
            "page": page,
            "items": items,
        }
        
        if extra:
            response.update(extra)
        
        return Response(response, status=status.HTTP_200_OK)
    
    @staticmethod
    def error(errors, message="", data=None, code=status.HTTP_400_BAD_REQUEST):
        """
        Ответ с ошибками
        
        Пример:
        {
            "success": false,
            "errors": ["Ошибка 1", "Ошибка 2"],
            "message": "Не удалось сохранить"
        }
        """
        if isinstance(errors, str):
            errors = [errors]
        
        response = {
            "success": False,
            "errors": errors,
        }
        
        if message:
            response["message"] = message
        
        if data:
            response["model"] = data
        
        return Response(response, status=code)
    
    @staticmethod
    def not_found(message="Ресурс не найден"):
        """Ответ 404"""
        return Response({
            "success": False,
            "errors": [],
            "message": message,
        }, status=status.HTTP_404_NOT_FOUND)
    
    @staticmethod
    def forbidden(message="Доступ запрещён"):
        """Ответ 403"""
        return Response({
            "success": False,
            "errors": [],
            "message": message,
        }, status=status.HTTP_403_FORBIDDEN)
    
    @staticmethod
    def unauthorized(message="Не авторизован"):
        """Ответ 401"""
        return Response({
            "success": False,
            "errors": [],
            "message": message,
        }, status=status.HTTP_401_UNAUTHORIZED)


class BaseAlfaModelMixin:
    """
    Миксин для моделей с методами для работы с API
    """
    
    def to_alfa_response(self, extra=None):
        """Преобразовать модель в формат ответа AlfaCRM"""
        data = self.__dict__.copy()
        data.pop('_state', None)
        data.pop('_str', None)
        
        if extra:
            data.update(extra)
        
        return {
            "id": self.id,
            **data
        }
    
    @classmethod
    def to_alfa_list(cls, queryset, extra_fields=None):
        """Преобразовать queryset в формат списка AlfaCRM"""
        items = []
        for obj in queryset:
            item = obj.to_alfa_response() if hasattr(obj, 'to_alfa_response') else obj.__dict__.copy()
            
            if extra_fields:
                for field_name, field_value in extra_fields.items():
                    if callable(field_value):
                        item[field_name] = field_value(obj)
                    else:
                        item[field_name] = field_value
            
            items.append(item)
        
        return items