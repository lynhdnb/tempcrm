from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('new/', views.create_enrollment, name='create_enrollment'),
    path('api/product-details/', views.get_product_details, name='product_details'),
    path('dashboard/', views.manager_dashboard, name='manager_dashboard'),
]
