from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect

from .models import Producto

carrito = {}  # {id_producto: cantidad} — en memoria, sin sesión ni base de datos


def obtener_carrito():
    productos = Producto.objects.in_bulk(carrito)
    return [
        {'producto': productos[producto_id], 'cantidad': cantidad}
        for producto_id, cantidad in carrito.items()
        if producto_id in productos
    ]


def usuario_actual(request):
    """Lee el usuario logeado desde las cookies del navegador (sin sesión, sin BD)."""
    nombre = request.COOKIES.get('nombre_usuario')
    rol = request.COOKIES.get('rol_usuario')
    if not nombre:
        return None
    return {'nombre': nombre, 'rol': rol}


def login_view(request):
    error = None
    if request.method == 'POST':
        nombre = request.POST.get('usuario', '').strip()
        if nombre:
            rol = 'admin' if nombre.lower() == 'admin' else 'cliente'
            respuesta = redirect('lista')
            respuesta.set_cookie('nombre_usuario', nombre, max_age=60 * 60 * 8)
            respuesta.set_cookie('rol_usuario', rol, max_age=60 * 60 * 8)
            return respuesta
        error = 'Debes ingresar un nombre.'
    return render(request, 'catalogo/login.html', {'error': error})


def logout_view(request):
    respuesta = redirect('login')
    respuesta.delete_cookie('nombre_usuario')
    respuesta.delete_cookie('rol_usuario')
    return respuesta


def lista(request):
    usuario = usuario_actual(request)
    if usuario is None:
        return redirect('login')

    productos_visibles = Producto.objects.all()
    if usuario['rol'] != 'admin':
        productos_visibles = productos_visibles.filter(activo=True)

    total_productos = productos_visibles.count()
    disponibles = productos_visibles.filter(stock__gt=0).count()

    resumen = {
        'total': total_productos,
        'disponibles': disponibles,
        'sin_stock': total_productos - disponibles,
    }

    contexto = {
        'productos': productos_visibles,
        'resumen': resumen,
        'carrito': obtener_carrito(),
        'usuario': usuario,
    }
    return render(request, 'catalogo/lista.html', contexto)


def detalle(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None:
        return redirect('login')

    producto = get_object_or_404(Producto, pk=producto_id)

    if not producto.activo and usuario['rol'] != 'admin':
        raise Http404("El producto solicitado no existe en el catálogo.")

    contexto = {
        'producto': producto,
        'carrito': obtener_carrito(),
        'usuario': usuario,
    }
    return render(request, 'detalles.html', contexto)


def comprar(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None:
        return redirect('login')

    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        actualizado = Producto.objects.filter(
            pk=producto.pk,
            activo=True,
            stock__gt=0,
        ).update(stock=F('stock') - 1)
        if actualizado:
            carrito[producto_id] = carrito.get(producto_id, 0) + 1

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def retirar(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None or usuario['rol'] != 'admin':
        return redirect('login')

    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        producto.activo = False
        producto.save(update_fields=['activo'])

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def reactivar(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None or usuario['rol'] != 'admin':
        return redirect('login')

    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        producto.activo = True
        producto.save(update_fields=['activo'])

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def agregar_stock(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None or usuario['rol'] != 'admin':
        return redirect('login')

    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', 1))
        except ValueError:
            cantidad = 0
        if cantidad > 0:
            Producto.objects.filter(pk=producto.pk).update(stock=F('stock') + cantidad)

    return redirect(request.META.get('HTTP_REFERER', 'lista'))