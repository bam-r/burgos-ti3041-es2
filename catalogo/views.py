import json
from pathlib import Path

from django.http import Http404
from django.shortcuts import render, redirect

DATA_PATH = Path(__file__).resolve().parent / 'data' / 'productos.json'

carrito = {}  # {id_producto: cantidad} — en memoria, sin sesión ni base de datos


def cargar_productos():
    with open(DATA_PATH, encoding='utf-8') as archivo:
        productos = json.load(archivo)
    for p in productos:
        p.setdefault('imagen', '/static/catalogo/img/sin-imagen.jpg')
        p.setdefault('activo', True)
    return productos


def guardar_productos(productos):
    with open(DATA_PATH, 'w', encoding='utf-8') as archivo:
        json.dump(productos, archivo, ensure_ascii=False, indent=2)


def obtener_carrito(productos):
    items = []
    for producto_id, cantidad in carrito.items():
        producto = next((p for p in productos if p['id'] == producto_id), None)
        if producto:
            items.append({'producto': producto, 'cantidad': cantidad})
    return items


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

    productos = cargar_productos()

    if usuario['rol'] == 'admin':
        productos_visibles = productos
    else:
        productos_visibles = [p for p in productos if p['activo']]

    total_productos = len(productos_visibles)
    disponibles = sum(1 for p in productos_visibles if p['stock'] > 0)

    resumen = {
        'total': total_productos,
        'disponibles': disponibles,
        'sin_stock': total_productos - disponibles,
    }

    contexto = {
        'productos': productos_visibles,
        'resumen': resumen,
        'carrito': obtener_carrito(productos),
        'usuario': usuario,
    }
    return render(request, 'catalogo/lista.html', contexto)


def detalle(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None:
        return redirect('login')

    productos = cargar_productos()
    producto = next((p for p in productos if p['id'] == producto_id), None)

    if producto is None:
        raise Http404("El producto solicitado no existe en el catálogo.")

    if not producto['activo'] and usuario['rol'] != 'admin':
        raise Http404("El producto solicitado no existe en el catálogo.")

    contexto = {
        'producto': producto,
        'carrito': obtener_carrito(productos),
        'usuario': usuario,
    }
    return render(request, 'catalogo/detalle.html', contexto)


def comprar(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None:
        return redirect('login')

    productos = cargar_productos()
    producto = next((p for p in productos if p['id'] == producto_id), None)

    if producto is None:
        raise Http404("El producto solicitado no existe en el catálogo.")

    if request.method == 'POST' and producto['activo'] and producto['stock'] > 0:
        producto['stock'] -= 1
        guardar_productos(productos)
        carrito[producto_id] = carrito.get(producto_id, 0) + 1

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def retirar(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None or usuario['rol'] != 'admin':
        return redirect('login')

    productos = cargar_productos()
    producto = next((p for p in productos if p['id'] == producto_id), None)

    if producto is None:
        raise Http404("El producto solicitado no existe en el catálogo.")

    if request.method == 'POST':
        producto['activo'] = False
        guardar_productos(productos)

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def reactivar(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None or usuario['rol'] != 'admin':
        return redirect('login')

    productos = cargar_productos()
    producto = next((p for p in productos if p['id'] == producto_id), None)

    if producto is None:
        raise Http404("El producto solicitado no existe en el catálogo.")

    if request.method == 'POST':
        producto['activo'] = True
        guardar_productos(productos)

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def agregar_stock(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None or usuario['rol'] != 'admin':
        return redirect('login')

    productos = cargar_productos()
    producto = next((p for p in productos if p['id'] == producto_id), None)

    if producto is None:
        raise Http404("El producto solicitado no existe en el catálogo.")

    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', 1))
        except ValueError:
            cantidad = 0
        if cantidad > 0:
            producto['stock'] += cantidad
            guardar_productos(productos)

    return redirect(request.META.get('HTTP_REFERER', 'lista'))