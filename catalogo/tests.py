from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Producto


class ProductoAdminCRUDTests(TestCase):
	def setUp(self):
		admin_user = get_user_model().objects.create_superuser(
			username='admin_test',
			email='admin@example.com',
			password='test-password',
		)
		self.client.force_login(admin_user)

	def test_admin_can_create_edit_and_delete_producto(self):
		self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)

		response = self.client.post(reverse('admin:catalogo_producto_add'), {
			'nombre': 'Producto temporal de prueba',
			'categoria': 'Pruebas',
			'precio': '1000',
			'stock': '2',
			'imagen': '/static/catalogo/img/sin-imagen.jpg',
			'activo': 'on',
			'_save': 'Guardar',
		})
		self.assertEqual(response.status_code, 302)
		producto = Producto.objects.get(nombre='Producto temporal de prueba')

		response = self.client.post(
			reverse('admin:catalogo_producto_change', args=[producto.pk]),
			{
				'nombre': producto.nombre,
				'categoria': 'Pruebas editado',
				'precio': '1500',
				'stock': '3',
				'imagen': producto.imagen,
				'activo': 'on',
				'_save': 'Guardar',
			},
		)
		self.assertEqual(response.status_code, 302)
		producto.refresh_from_db()
		self.assertEqual(producto.categoria, 'Pruebas editado')
		self.assertEqual(producto.precio, 1500)
		self.assertEqual(producto.stock, 3)

		delete_url = reverse('admin:catalogo_producto_delete', args=[producto.pk])
		self.assertEqual(self.client.get(delete_url).status_code, 200)
		response = self.client.post(delete_url, {'post': 'yes'})
		self.assertEqual(response.status_code, 302)
		self.assertFalse(Producto.objects.filter(pk=producto.pk).exists())
