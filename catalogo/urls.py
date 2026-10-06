from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista, name='lista'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('producto/<int:producto_id>/', views.detalle, name='detalle'),
    path('comprar/<int:producto_id>/', views.comprar, name='comprar'),
    path('retirar/<int:producto_id>/', views.retirar, name='retirar'),
    path('reactivar/<int:producto_id>/', views.reactivar, name='reactivar'),
    path('agregar-stock/<int:producto_id>/', views.agregar_stock, name='agregar_stock'),
]