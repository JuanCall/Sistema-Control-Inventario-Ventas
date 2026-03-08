import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.routes import router, get_db
from app import models
from app.database import engine

# Creamos las tablas físicas en la BD
models.Base.metadata.create_all(bind=engine)

# --- RUTAS ABSOLUTAS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Inicializamos la aplicación
app = FastAPI(title="Sistema de Inventario API V2")

# --- SEGURIDAD Y SESIONES ---
app.add_middleware(SessionMiddleware, secret_key="mancora2026_seguro")

# Le damos la ruta absoluta exacta a FastAPI
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(router)
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- FUNCIÓN PUENTE ---
def preparar_productos_para_html(db: Session):
    productos = db.query(models.Producto).all()
    for p in productos:
        lotes_activos = [l for l in p.lotes if l.activo]
        p.stock_actual = sum(l.stock_unidades for l in lotes_activos)
        if lotes_activos:
            lote_proximo = min(lotes_activos, key=lambda x: x.fecha_vencimiento)
            p.precio_costo_caja = lote_proximo.precio_costo_caja
            p.fecha_vencimiento = lote_proximo.fecha_vencimiento
        else:
            p.precio_costo_caja = 0
            p.fecha_vencimiento = ""
    return productos

# --- RUTAS DE LOGIN Y LOGOUT ---
@app.get("/login", tags=["Seguridad"])
def vista_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", tags=["Seguridad"])
def procesar_login(request: Request, pin: str = Form(...), db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.pin_seguridad == pin, models.Usuario.activo == True).first()
    if usuario:
        request.session["usuario_id"] = usuario.id_usuario
        request.session["nombre"] = usuario.nombre
        request.session["rol"] = usuario.rol
        
        # Si es admin, va al dashboard. Si es cajero, va directo a la caja.
        if usuario.rol == "admin":
            return RedirectResponse(url="/", status_code=303)
        else:
            return RedirectResponse(url="/punto_venta", status_code=303)
            
    return templates.TemplateResponse("login.html", {"request": request, "error": "PIN incorrecto"})

@app.get("/logout", tags=["Seguridad"])
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")

# --- RUTAS WEB PROTEGIDAS ---
@app.get("/", tags=["Interfaz Web"])
def vista_dashboard(request: Request, db: Session = Depends(get_db)):
    # Protección: Solo el admin puede ver esto
    if "rol" not in request.session:
        return RedirectResponse(url="/login")
    if request.session.get("rol") != "admin":
        return RedirectResponse(url="/punto_venta")

    productos_preparados = preparar_productos_para_html(db)
    
    total_productos = sum(1 for p in productos_preparados if p.activo)
    productos_bajo_stock = sum(1 for p in productos_preparados if p.activo and p.stock_actual < 20)
    
    ventas = db.query(models.Venta).all()
    total_ingresos = sum(venta.total_venta for venta in ventas)

    detalles_vendidos = db.query(models.DetalleVenta).all()
    total_gastos = 0
    for detalle in detalles_vendidos:
        producto = next((p for p in productos_preparados if p.id_producto == detalle.id_producto), None)
        if producto and getattr(producto, 'unidades_por_caja', 0) > 0 and getattr(producto, 'precio_costo_caja', 0):
            costo_por_unidad = producto.precio_costo_caja / producto.unidades_por_caja
            total_gastos += (costo_por_unidad * detalle.cantidad_unidades)
            
    ganancia_neta = total_ingresos - total_gastos

    alertas_stock = [p for p in productos_preparados if p.activo and p.stock_actual < 20][:5]

    # Lógica de Alertas de Vencimiento (Próximos 30 días)
    fecha_limite = datetime.now() + timedelta(days=30)
    lotes_por_vencer = db.query(models.Lote).join(models.Producto).filter(
        models.Lote.activo == True,
        models.Lote.fecha_vencimiento <= fecha_limite.date()
    ).order_by(models.Lote.fecha_vencimiento.asc()).all()

    ventas_dia = db.query(
        func.strftime('%Y-%m-%d', models.Venta.fecha_hora).label("fecha"),
        func.sum(models.Venta.total_venta).label("total")
    ).group_by(func.strftime('%Y-%m-%d', models.Venta.fecha_hora)).all()

    ventas_mes = db.query(
        func.strftime('%Y-%m', models.Venta.fecha_hora).label("fecha"),
        func.sum(models.Venta.total_venta).label("total")
    ).group_by(func.strftime('%Y-%m', models.Venta.fecha_hora)).all()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "total_productos": total_productos,
            "productos_bajo_stock": productos_bajo_stock,
            "total_ingresos": total_ingresos,
            "total_gastos": total_gastos,
            "ganancia_neta": ganancia_neta,
            "alertas_stock": alertas_stock,
            "lotes_por_vencer": lotes_por_vencer, # <-- Pasamos la data al HTML
            "fechas_dia": [v.fecha for v in ventas_dia],
            "totales_dia": [float(v.total) for v in ventas_dia],
            "fechas_mes": [v.fecha for v in ventas_mes],
            "totales_mes": [float(v.total) for v in ventas_mes]
        }
    )

@app.get("/inventario", tags=["Interfaz Web"])
def vista_inventario(request: Request, db: Session = Depends(get_db)):
    # Protección: Solo el admin puede ver el inventario
    if request.session.get("rol") != "admin":
        return RedirectResponse(url="/punto_venta")

    lista_productos = preparar_productos_para_html(db)
    lista_categorias = db.query(models.Categoria).filter(models.Categoria.activo == True).all()
    
    return templates.TemplateResponse(
        "inventario.html", 
        {"request": request, "productos": lista_productos, "categorias": lista_categorias}
    )

@app.get("/punto_venta", tags=["Interfaz Web"])
def vista_punto_venta(request: Request, db: Session = Depends(get_db)):
    # Protección: Debe estar logueado (cajero o admin)
    if "rol" not in request.session:
        return RedirectResponse(url="/login")

    lista_productos = preparar_productos_para_html(db)
    return templates.TemplateResponse(
        "punto_venta.html", 
        {"request": request, "productos": lista_productos}
    )