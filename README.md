# SystemSmart - Gestión de Inventario y Ventas (Edición Farmacia) 💊

**SistemaSmart** es una solución integral de punto de venta (POS) e inventario diseñada específicamente para pequeñas y medianas boticas y farmacias en Perú. El sistema permite un control riguroso de la mercadería, optimizando la rentabilidad mediante el seguimiento inteligente de lotes, integración de hardware estándar y control exacto de flujos de efectivo y billeteras digitales.

## 🚀 Características Principales

* **Motor de Inventario PEPS (FIFO):** Implementación automatizada del método "Primeras Entradas, Primeras Salidas", garantizando que los lotes con vencimiento más próximo se descuenten primero de forma transparente para el usuario.
* **Integración POS de Hardware:** Soporte nativo para **lectores de códigos de barras** (búsqueda y agregado ultrarrápido) e **impresión térmica de tickets** (formato 58mm) sin necesidad de drivers complejos.
* **Cuadre de Caja Híbrido:** Control diario separado para ventas en **Efectivo físico** y depósitos digitales (**Yape / Plin**), facilitando el cierre de caja nocturno.
* **Caja Registradora Inteligente:** Selector dinámico de presentaciones (Unidad, Blíster, Caja) y calculadora de vuelto en tiempo real para evitar errores humanos en mostrador.
* **Dashboard Financiero Directivo:** Visualización avanzada de Ingresos, Costo de Ventas, Utilidad Neta y alertas críticas (stock mínimo y próximos vencimientos) mediante gráficos dinámicos interactivos.
* **Seguridad y Roles:** Sistema de login por PIN con control de acceso (Administrador / Cajero) y manejo de zona horaria local (UTC-5) para registros precisos.
* **Arquitectura Local:** Funcionamiento 100% offline, ideal para zonas con conectividad inestable, garantizando la continuidad ininterrumpida del negocio.

## 🛠️ Stack Tecnológico

* **Backend:** Python 3.12 con **FastAPI**.
* **Base de Datos:** SQLite con **SQLAlchemy** (ORM).
* **Frontend:** HTML5, CSS3 (**Bootstrap 5**), Vanilla JavaScript.
* **Visualización de Datos:** **Chart.js**.
* **Motor de Plantillas:** Jinja2.

## 📦 Instalación y Despliegue

1. Clonar el repositorio o copiar la carpeta del proyecto.
2. Crear un entorno virtual: `python -m venv venv`
3. Activar el entorno virtual:
   * Windows: `venv\Scripts\activate`
   * Mac/Linux: `source venv/bin/activate`
4. Instalar las dependencias: `pip install -r requirements.txt`
5. **Inicializar la Base de Datos y Accesos:** Ejecutar el script de configuración inicial para generar los roles de prueba (Admin y Cajero):
   `python crear_accesos.py`
6. Iniciar el servidor local: `uvicorn app.main:app --reload`
7. Acceder en el navegador a: `http://127.0.0.1:8000`

---
Desarrollado por **Juan Anthony Calle Rosales** - Estudiante de Ingeniería de Sistemas.