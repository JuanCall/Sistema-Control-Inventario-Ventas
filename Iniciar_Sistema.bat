@echo off
title Motor del SistemaSmart - NO CERRAR
echo ======================================================
echo          SISTEMA DE INVENTARIO ACTIVO
echo ======================================================
echo.
echo Por favor, NO cierre esta ventana mientras la farmacia este abierta.
echo Puede minimizarla (-) para que no estorbe en la pantalla.
echo.
echo Al terminar el turno y cerrar la caja, cierre esta ventana (X).
echo.
call venv\Scripts\activate
start http://127.0.0.1:8000
uvicorn app.main:app