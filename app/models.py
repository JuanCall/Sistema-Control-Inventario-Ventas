from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# 1. Tabla Usuarios
class Usuario(Base):
    __tablename__ = "Usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    rol = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Relación: Un usuario puede tener muchas ventas
    ventas = relationship("Venta", back_populates="cajero")

# 2. Tabla Categorías
class Categoria(Base):
    __tablename__ = "Categorias"

    id_categoria = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    # Control para inhabilitar
    activo = Column(Boolean, default=True) 

    productos = relationship("Producto", back_populates="categoria")

# 3. Tabla Productos (Con la lógica de unidad mínima)
class Producto(Base):
    __tablename__ = "Productos"

    id_producto = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_categoria = Column(Integer, ForeignKey("Categorias.id_categoria"))
    nombre = Column(String(150), nullable=False)
    stock_actual = Column(Integer, nullable=False) # El sistema lo calculará
    unidades_por_blister = Column(Integer, default=1)
    unidades_por_caja = Column(Integer, default=1)
    precio_unidad = Column(Float, nullable=False)
    precio_blister = Column(Float)
    precio_caja = Column(Float)
    # Costo para calcular ganancias/gastos
    precio_costo_caja = Column(Float) 
    fecha_vencimiento = Column(Date)
    # Control para inhabilitar
    activo = Column(Boolean, default=True)

    categoria = relationship("Categoria", back_populates="productos")
    detalles_venta = relationship("DetalleVenta", back_populates="producto")

# 4. Tabla Ventas
class Venta(Base):
    __tablename__ = "Ventas"

    id_venta = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("Usuarios.id_usuario"))
    fecha_hora = Column(DateTime, default=datetime.utcnow)
    total_venta = Column(Float, nullable=False)

    # Relaciones
    cajero = relationship("Usuario", back_populates="ventas")
    detalles = relationship("DetalleVenta", back_populates="venta")

# 5. Tabla Detalle_Ventas
class DetalleVenta(Base):
    __tablename__ = "Detalle_Ventas"

    id_detalle = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_venta = Column(Integer, ForeignKey("Ventas.id_venta"))
    id_producto = Column(Integer, ForeignKey("Productos.id_producto"))
    cantidad_unidades = Column(Integer, nullable=False)
    precio_cobrado = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Relaciones
    venta = relationship("Venta", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_venta")