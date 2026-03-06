from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.database import SessionLocal
from app import models
from datetime import date
from typing import List, Optional

# 1. Inicializamos el "Enrutador" (agrupa todas nuestras URLs)
router = APIRouter()

# 2. Dependencia para conectarnos a la base de datos en cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. El Esquema (Pydantic): Define qué datos EXIGIMOS recibir desde internet
class CategoriaCreate(BaseModel):
    nombre: str

    class Config:
        orm_mode = True

# Este esquema es para LEER (hereda el nombre y le suma el ID)
class CategoriaResponse(CategoriaCreate):
    id_categoria: int

# Esquema para CREAR (Lo que el usuario envía desde el navegador)
class ProductoCreate(BaseModel):
    id_categoria: int
    nombre: str
    cantidad_cajas: int
    unidades_por_blister: int # OBLIGATORIO para hacer el cálculo
    unidades_por_caja: int    # OBLIGATORIO para hacer el cálculo
    precio_unidad: float
    precio_blister: Optional[float] = None
    precio_caja: Optional[float] = None
    precio_costo_caja: float  # NUEVO: Cuánto te costó
    fecha_vencimiento: Optional[date] = None

    class Config:
        orm_mode = True

# Esquema para RESPONDER (Lo que la API devuelve, incluyendo el ID generado)
class ProductoResponse(BaseModel):
    id_producto: int
    id_categoria: int
    nombre: str
    stock_actual: int # El sistema devuelve el stock ya calculado
    unidades_por_blister: int
    unidades_por_caja: int
    precio_unidad: float
    precio_blister: Optional[float]
    precio_caja: Optional[float]
    precio_costo_caja: Optional[float]
    fecha_vencimiento: Optional[date]
    activo: bool

    class Config:
        orm_mode = True

# --- ESQUEMAS DE VENTAS ---
class DetalleVentaCreate(BaseModel):
    id_producto: int
    cantidad: int

class VentaCreate(BaseModel):
    id_usuario: int = 1
    detalles: List[DetalleVentaCreate]

# 4. LA RUTA: Recibe la información y la guarda en la base de datos
@router.post("/categorias/", tags=["Categorías"])
def crear_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    # A. Preparamos el modelo de Python con los datos que llegaron
    nueva_categoria = models.Categoria(nombre=categoria.nombre)
    
    # B. Lo agregamos a la base de datos
    db.add(nueva_categoria)
    
    # C. Confirmamos los cambios (como darle a "Guardar")
    db.commit()
    
    # D. Refrescamos para obtener el ID que SQLite le asignó automáticamente
    db.refresh(nueva_categoria)
    
    # E. Devolvemos la categoría recién creada al navegador
    return nueva_categoria

# 5. RUTA PARA LISTAR: Obtiene todas las categorías guardadas
@router.get("/categorias/", response_model=List[CategoriaResponse], tags=["Categorías"])
def obtener_categorias(db: Session = Depends(get_db)):
    # Simplemente le pedimos a la sesión que busque todos los registros de la clase Categoria
    categorias = db.query(models.Categoria).all()
    
    # Python y FastAPI se encargan de convertir esa lista de objetos a JSON automáticamente
    return categorias

# --- RUTAS PARA PRODUCTOS ---

# 1. Actualizar Producto Existente
@router.put("/productos/{id_producto}", tags=["Productos"])
def actualizar_producto(id_producto: int, producto: ProductoCreate, db: Session = Depends(get_db)):
    db_producto = db.query(models.Producto).filter(models.Producto.id_producto == id_producto).first()
    
    db_producto.id_categoria = producto.id_categoria
    db_producto.nombre = producto.nombre
    # Recalculamos el stock basado en las nuevas cajas
    db_producto.stock_actual = producto.cantidad_cajas * producto.unidades_por_caja
    db_producto.unidades_por_blister = producto.unidades_por_blister
    db_producto.unidades_por_caja = producto.unidades_por_caja
    db_producto.precio_unidad = producto.precio_unidad
    db_producto.precio_blister = producto.precio_blister
    db_producto.precio_caja = producto.precio_caja
    db_producto.precio_costo_caja = producto.precio_costo_caja
    db_producto.fecha_vencimiento = producto.fecha_vencimiento
    
    db.commit()
    return {"mensaje": "Producto actualizado con éxito"}

# 2. Inhabilitar Producto (Soft Delete)
@router.delete("/productos/{id_producto}", tags=["Productos"])
def inhabilitar_producto(id_producto: int, db: Session = Depends(get_db)):
    db_producto = db.query(models.Producto).filter(models.Producto.id_producto == id_producto).first()
    db_producto.activo = False # Lo ocultamos, pero no lo borramos de la base de datos
    db.commit()
    return {"mensaje": "Producto inhabilitado"}

# 3. RUTA PARA CREAR PRODUCTO
@router.post("/productos/", response_model=ProductoResponse, tags=["Productos"])
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    
    # 1. El sistema calcula las unidades totales automáticamente
    stock_calculado = producto.cantidad_cajas * producto.unidades_por_caja
    
    # 2. Preparamos el modelo para la base de datos
    nuevo_producto = models.Producto(
        id_categoria=producto.id_categoria,
        nombre=producto.nombre,
        stock_actual=stock_calculado, # Inyectamos la matemática aquí
        unidades_por_blister=producto.unidades_por_blister,
        unidades_por_caja=producto.unidades_por_caja,
        precio_unidad=producto.precio_unidad,
        precio_blister=producto.precio_blister,
        precio_caja=producto.precio_caja,
        precio_costo_caja=producto.precio_costo_caja,
        fecha_vencimiento=producto.fecha_vencimiento
    )
    
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    
    return nuevo_producto

# 4. RUTA PARA LISTAR: Obtiene todos los productos guardados
@router.get("/productos/", response_model=List[ProductoResponse], tags=["Productos"])
def obtener_productos(db: Session = Depends(get_db)):
    productos = db.query(models.Producto).all()
    return productos


# 8. RUTA PARA COBRAR LA VENTA
@router.post("/ventas/", tags=["Ventas"])
def registrar_venta(venta: VentaCreate, db: Session = Depends(get_db)):
    total_venta = 0
    
    # Paso 1: Creamos el recibo general (aún en S/ 0.00)
    nueva_venta = models.Venta(id_usuario=venta.id_usuario, total_venta=0)
    db.add(nueva_venta)
    db.flush() # Guardamos temporalmente para obtener el id_venta generado
    
    # Paso 2: Procesamos cada producto que llegó en el carrito
    for item in venta.detalles:
        # Buscamos el producto en la base de datos
        producto_db = db.query(models.Producto).filter(models.Producto.id_producto == item.id_producto).first()
        
        # Validación de seguridad: ¿Hay suficiente stock?
        if producto_db.stock_actual < item.cantidad:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para el producto {producto_db.nombre}")
            
        # Descontamos el stock
        producto_db.stock_actual -= item.cantidad
        
        # Calculamos la matemática real (por seguridad, no confiamos en el precio del HTML)
        subtotal_item = producto_db.precio_unidad * item.cantidad
        total_venta += subtotal_item
        
        # Creamos el detalle de esta línea del recibo
        nuevo_detalle = models.DetalleVenta(
            id_venta=nueva_venta.id_venta,
            id_producto=item.id_producto,
            cantidad_unidades=item.cantidad,
            precio_cobrado=producto_db.precio_unidad,
            subtotal=subtotal_item
        )
        db.add(nuevo_detalle)
        
    # Paso 3: Actualizamos el recibo con el total verdadero y confirmamos todo en SQLite
    nueva_venta.total_venta = total_venta
    db.commit()
    
    return {"mensaje": "Venta exitosa", "total": total_venta}

# --- RUTAS PARA CATEGORÍAS ---

# 1. Crear Categoría desde el sistema (para no usar Swagger)
@router.post("/categorias/", tags=["Categorias"])
def crear_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    nueva_categoria = models.Categoria(nombre=categoria.nombre)
    db.add(nueva_categoria)
    db.commit()
    return {"mensaje": "Categoría creada con éxito"}

# 2. Inhabilitar Categoría
@router.delete("/categorias/{id_categoria}", tags=["Categorias"])
def inhabilitar_categoria(id_categoria: int, db: Session = Depends(get_db)):
    db_categoria = db.query(models.Categoria).filter(models.Categoria.id_categoria == id_categoria).first()
    db_categoria.activo = False
    db.commit()
    return {"mensaje": "Categoría inhabilitada"}