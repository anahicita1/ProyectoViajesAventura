# Informe de auditoría crítica de IA

## Propósito

Documentar el uso de IA durante el diseño y construcción del sistema, reconociendo riesgos y decisiones técnicas aplicadas para minimizar vulnerabilidades y mantener consistencia con la rúbrica.

## Sugerencias recibidas desde IA

- Modularizar proyecto en capas: modelos, repositorios, servicios, vistas y utilidades.
- Separar autenticación y reglas de negocio de la capa de presentación.
- Usar SQLite con PRAGMA foreign_keys = ON.
- Aplicar validaciones en la base de datos y en el servicio antes de confirmar reservas.
- Diseñar sistema con autenticación PBKDF2-HMAC-SHA256 y bloqueo por intentos fallidos.

## Riesgos identificados

- OWASP: credenciales mal guardadas o uso de hashing débil.
- Condiciones de carrera al reservar cupos simultáneamente.
- Duplicidad de reservas por cliente y paquete.
- Flotantes o decimales incorrectos para valores monetarios.
- Validaciones sin control en la capa View.
- Uso inadecuado de SQL concatenado.

## Refactorizaciones aplicadas

- Se implementó hashing PBKDF2-HMAC-SHA256 con salt aleatorio.
- Se añadieron transacciones SQL atómicas y comprobación de cupos dentro de la misma transacción.
- Se usó índice parcial único para evitar reservas duplicadas confirmadas.
- Se congeló el precio al publicar el paquete.
- Se usó borrado lógico de destinos con `activo = 0`.
- Se evitó SQL dinámico concatenado en repositorios.
- Se documentaron reglas de negocio en servicios y en la base de datos.

## Respuesta responsable

El sistema se desarrolló con el objetivo de ser coherente, seguro y verificable. Las decisiones tomadas están alineadas con la normativa de seguridad y calidad académica del caso de estudio, sin ocultar riesgos ni asumir validaciones que no estén respaldadas por la base de datos.
