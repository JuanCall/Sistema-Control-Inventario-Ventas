import random
from datetime import datetime, timedelta
from app.database import SessionLocal, engine
from app import models

# Aseguramos que las tablas existan con las nuevas columnas
models.Base.metadata.create_all(bind=engine)

# Abrimos conexión directa con tu base de datos
db = SessionLocal()

print("⏳ Viajando en el tiempo para generar ventas y yapeos desde Enero 2026...")

def poblar_datos():
    # 1. Crear Cajero de prueba (si no existe)
    cajero = db.query(models.Usuario).first()
    if not cajero:
        cajero = models.Usuario(nombre="Juan (Admin)", pin_seguridad="1234", rol="admin")
        db.add(cajero)
        db.commit()

    # 2. Crear un par de categorías de Farmacia
    categorias = ["Antibióticos", "Vitaminas", "Primeros Auxilios"]
    cats_db = []
    for nombre in categorias:
        cat = db.query(models.Categoria).filter_by(nombre=nombre).first()
        if not cat:
            cat = models.Categoria(nombre=nombre)
            db.add(cat)
            db.commit()
            db.refresh(cat)
        cats_db.append(cat)

    # 3. Crear Productos con Códigos de Barras Falsos
    productos_data = [
        {"nombre": "Amoxicilina 500mg", "cat": cats_db[0].id_categoria, "costo": 15.0, "precio": 1.5, "cajas": 5, "codigo": "775001"},
        {"nombre": "Vitamina C + Zinc", "cat": cats_db[1].id_categoria, "costo": 25.0, "precio": 2.5, "cajas": 8, "codigo": "775002"},
        {"nombre": "Alcohol en gel 1L", "cat": cats_db[2].id_categoria, "costo": 10.0, "precio": 18.0, "cajas": 12, "u_caja": 1, "codigo": "775003"}
    ]
    
    productos_db = []
    for pd in productos_data:
        prod = db.query(models.Producto).filter_by(nombre=pd["nombre"]).first()
        u_caja = pd.get("u_caja", 100)
        
        if not prod:
            prod = models.Producto(
                id_categoria=pd["cat"],
                nombre=pd["nombre"],
                codigo_barras=pd["codigo"],
                unidades_por_blister=10 if u_caja > 1 else 1,
                unidades_por_caja=u_caja,
                precio_unidad=pd["precio"],
                precio_blister=pd["precio"]*10 if u_caja > 1 else 0,
                precio_caja=pd["precio"]*u_caja
            )
            db.add(prod)
            db.commit()
            db.refresh(prod)
            
            # Lote creado en Enero
            lote = models.Lote(
                id_producto=prod.id_producto,
                stock_unidades=pd["cajas"] * u_caja,
                precio_costo_caja=pd["costo"],
                fecha_ingreso=datetime(2026, 1, 2),
                fecha_vencimiento=datetime(2027, random.randint(6, 12), 28)
            )
            db.add(lote)
            db.commit()
        productos_db.append(prod)

    # 4. SIMULAR LAS VENTAS
    fecha_inicio = datetime(2025, 1, 1)
    fecha_fin = datetime(2026, 3, 12)
    dias_totales = (fecha_fin - fecha_inicio).days
    
    ventas_creadas = 0
    
    for i in range(dias_totales + 1):
        fecha_actual = fecha_inicio + timedelta(days=i)
        
        for _ in range(random.randint(1, 6)):
            hora = random.randint(8, 20)
            minuto = random.randint(0, 59)
            fecha_venta = fecha_actual.replace(hour=hora, minute=minuto)
            
            # MAGIA: 30% de probabilidad de que paguen con Yape, 70% Efectivo
            metodo = random.choices(["Efectivo", "Yape"], weights=[0.7, 0.3])[0]
            
            nueva_venta = models.Venta(
                id_usuario=cajero.id_usuario, 
                fecha_hora=fecha_venta, 
                total_venta=0,
                metodo_pago=metodo # <-- SE GUARDA EL MÉTODO
            )
            db.add(nueva_venta)
            db.flush()
            
            total_ticket = 0
            productos_en_ticket = random.sample(productos_db, random.randint(1, 3))
            
            for p in productos_en_ticket:
                cantidad_vendida = random.randint(1, 4)
                subtotal = p.precio_unidad * cantidad_vendida
                total_ticket += subtotal
                
                detalle = models.DetalleVenta(
                    id_venta=nueva_venta.id_venta,
                    id_producto=p.id_producto,
                    cantidad_unidades=cantidad_vendida,
                    precio_unitario_cobrado=p.precio_unidad
                )
                db.add(detalle)
                
            nueva_venta.total_venta = total_ticket
            db.commit()
            ventas_creadas += 1

    print(f"✅ ¡Completado! Se inyectaron {ventas_creadas} ventas falsas (con Efectivo y Yape) en tu base de datos.")

# Ejecutar la función
poblar_datos()