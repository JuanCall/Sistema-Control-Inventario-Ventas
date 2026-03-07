@echo off
echo Iniciando SistemaSmart... Por favor no cierre esta ventana negra.
call venv\Scripts\activate
start http://127.0.0.1:8000
uvicorn app.main:app