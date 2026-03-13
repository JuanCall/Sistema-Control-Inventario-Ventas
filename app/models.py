from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.database import Base

# Función para obtener siempre la hora exacta de Perú (UTC -5)
def hora_peru():
    return datetime.utcnow() - timedelta(hours=5)

# ==========================================
# TABLA USUARIOS
# ==========================================
class Usuario(Base):
    __tablename__ = "Usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    pin_seguridad = Column(String(4), nullable=False)
    rol = Column(String(20), default="cajero")
    activo = Column(Boolean, default=True)

    ventas = relationship("Venta", back_populates="cajero")

# ==========================================
# TABLA CATEGORIAS
# ==========================================
class Categoria(Base):
    __tablename__ = "Categorias"

    id_categoria = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    activo = Column(Boolean, default=True)

    productos = relationship("Producto", back_populates="categoria")

# ==========================================
# TABLA PRODUCTOS
# ==========================================
class Producto(Base):
    __tablename__ = "Productos"

    id_producto = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_categoria = Column(Integer, ForeignKey("Categorias.id_categoria"))
    codigo_barras = Column(String, unique=True, index=True, nullable=True)
    nombre = Column(String, index=True)
    
    # Presentaciones y precios de venta al público
    unidades_por_blister = Column(Integer, default=1)
    unidades_por_caja = Column(Integer, default=1)
    precio_unidad = Column(Float, nullable=False)
    precio_blister = Column(Float)
    precio_caja = Column(Float)
    
    activo = Column(Boolean, default=True)

    categoria = relationship("Categoria", back_populates="productos")
    detalles_venta = relationship("DetalleVenta", back_populates="producto")
    
    # Un producto puede tener muchos lotes diferentes
    lotes = relationship("Lote", back_populates="producto")

# ==========================================
# TABLA LOTES
# ==========================================
class Lote(Base):
    __tablename__ = "Lotes"

    id_lote = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_producto = Column(Integer, ForeignKey("Productos.id_producto"))
    
    # Inventario y Costos específicos de esta compra
    stock_unidades = Column(Integer, nullable=False) # Cuántas pastillas quedan de este lote
    precio_costo_caja = Column(Float, nullable=False) # Cuánto costó esta vez
    
    # Fechas clave para el método PEPS (FIFO)
    fecha_ingreso = Column(DateTime, default=datetime.utcnow)
    fecha_vencimiento = Column(Date, nullable=False)
    
    # Se volverá False automáticamente cuando el stock llegue a 0
    activo = Column(Boolean, default=True) 

    producto = relationship("Producto", back_populates="lotes")

# ==========================================
# TABLA VENTAS
# ==========================================
class Venta(Base):
    __tablename__ = "Ventas"

    id_venta = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("Usuarios.id_usuario"))
    fecha_hora = Column(DateTime, default=hora_peru)
    total_venta = Column(Float, nullable=False)
    metodo_pago = Column(String, default="Efectivo")

    cajero = relationship("Usuario", back_populates="ventas")
    detalles = relationship("DetalleVenta", back_populates="venta")

# ==========================================
# TABLA DETALLE DE VENTAS
# ==========================================
class DetalleVenta(Base):
    __tablename__ = "DetallesVenta"

    id_detalle = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_venta = Column(Integer, ForeignKey("Ventas.id_venta"))
    id_producto = Column(Integer, ForeignKey("Productos.id_producto"))
    cantidad_unidades = Column(Integer, nullable=False)
    precio_unitario_cobrado = Column(Float, nullable=False)
    
    venta = relationship("Venta", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_venta")