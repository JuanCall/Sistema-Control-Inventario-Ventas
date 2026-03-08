from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import SessionLocal
from app import models
from datetime import date

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CategoriaCreate(BaseModel):
    nombre: str
    class Config: orm_mode = True

class CategoriaResponse(CategoriaCreate):
    id_categoria: int

# Esquema para crear un Producto + su primer Lote
class ProductoCreate(BaseModel):
    id_categoria: int
    nombre: str
    cantidad_cajas_inicial: int # Para el primer lote
    unidades_por_blister: int
    unidades_por_caja: int
    precio_unidad: float
    precio_blister: Optional[float] = None
    precio_caja: Optional[float] = None
    precio_costo_caja: float # Costo de este primer lote
    fecha_vencimiento: date  # Vencimiento de este primer lote

class DetalleVentaCreate(BaseModel):
    id_producto: int
    cantidad: int

class VentaCreate(BaseModel):
    id_usuario: int = 1
    detalles: List[DetalleVentaCreate]

# --- RUTAS DE CATEGORÍAS ---
@router.post("/categorias/", tags=["Categorías"])
def crear_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    nueva_categoria = models.Categoria(nombre=categoria.nombre)
    db.add(nueva_categoria)
    db.commit()
    db.refresh(nueva_categoria)
    return nueva_categoria

@router.get("/categorias/", response_model=List[CategoriaResponse], tags=["Categorías"])
def obtener_categorias(db: Session = Depends(get_db)):
    return db.query(models.Categoria).filter(models.Categoria.activo == True).all()

@router.delete("/categorias/{id_categoria}", tags=["Categorias"])
def inhabilitar_categoria(id_categoria: int, db: Session = Depends(get_db)):
    db_cat = db.query(models.Categoria).filter(models.Categoria.id_categoria == id_categoria).first()
    db_cat.activo = False
    db.commit()
    return {"mensaje": "Categoría inhabilitada"}

@router.put("/categorias/{id_categoria}/habilitar", tags=["Categorias"])
def habilitar_categoria(id_categoria: int, db: Session = Depends(get_db)):
    db_cat = db.query(models.Categoria).filter(models.Categoria.id_categoria == id_categoria).first()
    db_cat.activo = True
    db.commit()
    return {"mensaje": "Categoría restaurada"}

# --- RUTAS DE PRODUCTOS Y LOTES ---

# ==========================================
# RUTAS DE LOTES (COMPRAS NUEVAS V2)
# ==========================================
class LoteCreate(BaseModel):
    id_producto: int
    cantidad_cajas: int
    precio_costo_caja: float
    fecha_vencimiento: date

@router.post("/lotes/", tags=["Lotes"])
def registrar_nuevo_lote(lote: LoteCreate, db: Session = Depends(get_db)):
    # 1. Buscamos cuántas unidades trae la caja de este producto
    producto = db.query(models.Producto).filter(models.Producto.id_producto == lote.id_producto).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    # 2. Calculamos las pastillas totales que están entrando
    unidades_ingresadas = lote.cantidad_cajas * producto.unidades_por_caja
    
    # 3. Creamos el lote físico
    nuevo_lote = models.Lote(
        id_producto=lote.id_producto,
        stock_unidades=unidades_ingresadas,
        precio_costo_caja=lote.precio_costo_caja,
        fecha_vencimiento=lote.fecha_vencimiento
    )
    db.add(nuevo_lote)
    db.commit()
    
    return {"mensaje": "Nuevo lote de mercadería registrado con éxito"}

@router.post("/productos/", tags=["Productos"])
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    # 1. Creamos el catálogo base (sin stock)
    nuevo_producto = models.Producto(
        id_categoria=producto.id_categoria,
        nombre=producto.nombre,
        unidades_por_blister=producto.unidades_por_blister,
        unidades_por_caja=producto.unidades_por_caja,
        precio_unidad=producto.precio_unidad,
        precio_blister=producto.precio_blister,
        precio_caja=producto.precio_caja
    )
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)

    # 2. Creamos su PRIMER LOTE con las cantidades y fechas
    unidades_totales = producto.cantidad_cajas_inicial * producto.unidades_por_caja
    primer_lote = models.Lote(
        id_producto=nuevo_producto.id_producto,
        stock_unidades=unidades_totales,
        precio_costo_caja=producto.precio_costo_caja,
        fecha_vencimiento=producto.fecha_vencimiento
    )
    db.add(primer_lote)
    db.commit()
    
    return {"mensaje": "Producto y Lote 1 creados con éxito"}

@router.put("/productos/{id_producto}", tags=["Productos"])
def actualizar_producto(id_producto: int, producto: ProductoCreate, db: Session = Depends(get_db)):
    # V2: Editar un producto solo actualiza sus nombres y precios de venta.
    db_producto = db.query(models.Producto).filter(models.Producto.id_producto == id_producto).first()
    db_producto.id_categoria = producto.id_categoria
    db_producto.nombre = producto.nombre
    db_producto.unidades_por_blister = producto.unidades_por_blister
    db_producto.unidades_por_caja = producto.unidades_por_caja
    db_producto.precio_unidad = producto.precio_unidad
    db_producto.precio_blister = producto.precio_blister
    db_producto.precio_caja = producto.precio_caja
    db.commit()
    return {"mensaje": "Datos generales del producto actualizados"}

@router.delete("/productos/{id_producto}", tags=["Productos"])
def inhabilitar_producto(id_producto: int, db: Session = Depends(get_db)):
    db_producto = db.query(models.Producto).filter(models.Producto.id_producto == id_producto).first()
    db_producto.activo = False
    db.commit()
    return {"mensaje": "Producto inhabilitado"}

@router.put("/productos/{id_producto}/habilitar", tags=["Productos"])
def habilitar_producto(id_producto: int, db: Session = Depends(get_db)):
    db_prod = db.query(models.Producto).filter(models.Producto.id_producto == id_producto).first()
    db_prod.activo = True
    db.commit()
    return {"mensaje": "Producto restaurado"}

# --- RUTA DE VENTAS (MÉTODO PEPS / FIFO) ---
@router.post("/ventas/", tags=["Ventas"])
def registrar_venta(venta: VentaCreate, db: Session = Depends(get_db)):
    total_venta = 0
    nueva_venta = models.Venta(id_usuario=venta.id_usuario, total_venta=0)
    db.add(nueva_venta)
    db.flush() 
    
    for item in venta.detalles:
        producto_db = db.query(models.Producto).filter(models.Producto.id_producto == item.id_producto).first()
        
        # Obtenemos TODOS los lotes activos de este producto, ordenados por fecha de vencimiento (el más viejo primero)
        lotes_activos = db.query(models.Lote).filter(
            models.Lote.id_producto == item.id_producto,
            models.Lote.activo == True
        ).order_by(models.Lote.fecha_vencimiento.asc()).all()
        
        stock_total = sum(l.stock_unidades for l in lotes_activos)
        
        if stock_total < item.cantidad:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para {producto_db.nombre}. Disponible: {stock_total}")
            
        unidades_a_descontar = item.cantidad
        
        # ALGORITMO PEPS: Descontamos lote por lote
        for lote in lotes_activos:
            if unidades_a_descontar <= 0:
                break
                
            if lote.stock_unidades <= unidades_a_descontar:
                # Vaciamos este lote por completo
                unidades_a_descontar -= lote.stock_unidades
                lote.stock_unidades = 0
                lote.activo = False # El lote murió
            else:
                # El lote tiene suficientes para cubrir lo que falta
                lote.stock_unidades -= unidades_a_descontar
                unidades_a_descontar = 0
                
        # Calculamos ingresos
        subtotal_item = producto_db.precio_unidad * item.cantidad
        total_venta += subtotal_item
        
        nuevo_detalle = models.DetalleVenta(
            id_venta=nueva_venta.id_venta,
            id_producto=item.id_producto,
            cantidad_unidades=item.cantidad,
            precio_unitario_cobrado=producto_db.precio_unidad
        )
        db.add(nuevo_detalle)
        
    nueva_venta.total_venta = total_venta
    db.commit()
    return {"mensaje": "Venta exitosa con descuento PEPS", "total": total_venta}