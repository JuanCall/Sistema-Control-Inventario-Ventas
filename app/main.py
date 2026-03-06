from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.routes import router, get_db
from app import models
from app.database import engine

# Esta es la línea que crea las tablas físicas
models.Base.metadata.create_all(bind=engine)

# Inicializamos la aplicación
app = FastAPI(title="Sistema de Inventario API")

# Conectamos las rutas a la aplicación principal
app.include_router(router)

# Configuramos la carpeta donde están nuestros archivos HTML
templates = Jinja2Templates(directory="templates")

# RUTA DEL DASHBOARD FINANCIERO
@app.get("/", tags=["Interfaz Web"])
def vista_dashboard(request: Request, db: Session = Depends(get_db)):
    # 1. Estadísticas Generales (Solo contamos productos activos)
    total_productos = db.query(models.Producto).filter(models.Producto.activo == True).count()
    productos_bajo_stock = db.query(models.Producto).filter(models.Producto.stock_actual < 20, models.Producto.activo == True).count()
    
    # 2. Cálculos Financieros
    ventas = db.query(models.Venta).all()
    total_ingresos = sum(venta.total_venta for venta in ventas)

    # NUEVO: Calcular los Gastos (Costo de la mercadería vendida)
    detalles_vendidos = db.query(models.DetalleVenta).all()
    total_gastos = 0
    for detalle in detalles_vendidos:
        producto = db.query(models.Producto).filter(models.Producto.id_producto == detalle.id_producto).first()
        # Verificamos que el producto tenga configurado un costo y unidades de caja
        if producto and producto.unidades_por_caja > 0 and producto.precio_costo_caja:
            costo_por_unidad = producto.precio_costo_caja / producto.unidades_por_caja
            total_gastos += (costo_por_unidad * detalle.cantidad_unidades)
    
    # NUEVO: La Ganancia Real
    ganancia_neta = total_ingresos - total_gastos

    alertas_stock = db.query(models.Producto).filter(models.Producto.stock_actual < 20, models.Producto.activo == True).limit(5).all()

    # --- DATOS PARA LA GRÁFICA ---
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
            "total_gastos": total_gastos,       # <-- Enviamos los gastos calculados
            "ganancia_neta": ganancia_neta,     # <-- Enviamos la ganancia real
            "alertas_stock": alertas_stock,
            "fechas_dia": [v.fecha for v in ventas_dia],
            "totales_dia": [float(v.total) for v in ventas_dia],
            "fechas_mes": [v.fecha for v in ventas_mes],
            "totales_mes": [float(v.total) for v in ventas_mes]
        }
    )

# Ruta para la interfaz visual del inventario
@app.get("/inventario", tags=["Interfaz Web"])
def vista_inventario(request: Request, db: Session = Depends(get_db)):
    # Pedimos productos y categorías a SQLite
    lista_productos = db.query(models.Producto).all()
    lista_categorias = db.query(models.Categoria).all() # <-- NUEVO
    
    # Enviamos ambas listas al HTML
    return templates.TemplateResponse(
        "inventario.html", 
        {
            "request": request, 
            "productos": lista_productos,
            "categorias": lista_categorias # <-- NUEVO
        }
    )

# Ruta para la pantalla de la Caja Registradora
@app.get("/punto_venta", tags=["Interfaz Web"])
def vista_punto_venta(request: Request, db: Session = Depends(get_db)):
    lista_productos = db.query(models.Producto).all()
    
    return templates.TemplateResponse(
        "punto_venta.html", 
        {"request": request, "productos": lista_productos}
    )