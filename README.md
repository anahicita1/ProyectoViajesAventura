# ProyectoViajesAventura

Sistema de reservas de paquetes turísticos desarrollado en Python con SQLite, Streamlit y servicios de negocio modularizados.

## Objetivo

Gestionar clientes, paquetes, destinos, reservas, validaciones de negocio y seguridad con autenticación mediante PBKDF2-HMAC-SHA256.

## Estructura principal

- config/
- models/
- repositories/
- services/
- utils/
- views/
- tests/
- app.py
- bootstrap.py

## Requisitos críticos cubiertos

- Índice único parcial para evitar reservas duplicadas confirmadas.
- Validación de cupos en transacción atómica.
- Filtro de fechas vencidas antes de reservar.
- Congelamiento de precios en paquetes publicados.
- Eliminación lógica de destinos activos/inactivos.
- Autenticación segura con PBKDF2-HMAC-SHA256 y bloqueo por intentos fallidos.
- Streamlit con sesiones y autenticación de roles.

## Ejecución local

1. Crear entorno virtual.
2. Instalar dependencias: `pip install -r requirements.txt`
3. Ejecutar la aplicación: `streamlit run app.py`

## Informe de auditoría de IA

Se puede consultar el reporte detallado en `docs/AI_AUDIT_REPORT.md`.
