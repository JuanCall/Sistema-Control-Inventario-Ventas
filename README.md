# SistemaSmart - Gestión de Inventario y Ventas (Edición Farmacia) 💊

**SistemaSmart** es una solución integral de punto de venta (POS) e inventario diseñada específicamente para pequeñas y medianas farmacias. El sistema permite un control riguroso de la mercadería, optimizando la rentabilidad mediante el seguimiento inteligente de lotes y fechas de vencimiento.

## 🚀 Características Principales

* **Motor de Inventario PEPS (FIFO):** Implementación del método "Primeras Entradas, Primeras Salidas", garantizando que los lotes con vencimiento más próximo se descuenten primero automáticamente.
* **Gestión de Lotes:** Control detallado por cada ingreso de mercadería, permitiendo múltiples costos y fechas de vencimiento para un mismo producto.
* **Punto de Venta (POS) Interactivo:** Buscador en tiempo real y selector dinámico de presentaciones (Unidad, Blíster, Caja) con recálculo automático de stock.
* **Dashboard Financiero:** Visualización avanzada de Ingresos, Gastos (Costo de ventas) y Utilidad Neta mediante gráficos dinámicos de líneas (Chart.js).
* **Arquitectura Local:** Funcionamiento 100% offline, ideal para zonas con conectividad inestable, garantizando la continuidad del negocio.

## 🛠️ Stack Tecnológico

* **Backend:** Python con **FastAPI**.
* **Base de Datos:** SQLite con **SQLAlchemy** (ORM).
* **Frontend:** HTML5, CSS3 (**Bootstrap 5**), JavaScript.
* **Visualización de Datos:** **Chart.js**.
* **Plantillas:** Jinja2.

## 📦 Instalación y Uso

1. Clonar el repositorio.
2. Crear un entorno virtual: `python -m venv venv`.
3. Activar el entorno e instalar dependencias: `pip install -r requirements.txt`.
4. Ejecutar el servidor: `uvicorn app.main:app --reload`.
5. Acceder a `http://127.0.0.1:8000`.

---
Desarrollado por **Juan Anthony Calle Rosales** - Estudiante de Ingeniería de Sistemas.