# WhatsApp PyME Bot · lectura de portafolio

Backend multiempresa para responder consultas de catálogo, conservar conversaciones y registrar intención de compra.

**Autor:** Jimmy Toapanta · [Perfil profesional](https://www.linkedin.com/in/jimmy-toapanta-950a441b8/) · [Portafolio](https://github.com/eslay07)

**Tecnologías:** Python · FastAPI · SQLAlchemy · Alembic · WhatsApp Cloud API

## Problema y solución

El volumen de preguntas repetidas aumenta el trabajo de atención y exige separar los datos de cada empresa.

Recibe webhooks, identifica la empresa, consulta su catálogo, conserva contexto y utiliza un motor local con IA opcional. Incluye simulación local y pruebas.

## Evidencia para revisar el trabajo

| Archivo o componente | Qué permite revisar |
| --- | --- |
| [app/main.py](app/main.py) | Composición de la API. |
| [app/routes/webhook.py](app/routes/webhook.py) | Recepción y validación de eventos. |
| [app/services/conversation_service.py](app/services/conversation_service.py) | Orquestación de conversaciones. |
| [app/services/security_service.py](app/services/security_service.py) | Protección de secretos configurados. |
| [tests/test_webhook.py](tests/test_webhook.py) | Casos de prueba del webhook. |

## Estado y límites

La integración real requiere configuración de Meta y despliegue. El simulador permite revisar el recorrido sin enviar mensajes externos; no se afirma aquí un despliegue de producción auditado.

## Cómo evaluar el proyecto

Seguir el README para ejecutar el simulador y las pruebas con servicios simulados. No se enviaron mensajes, pagos ni pedidos reales durante la revisión.

Esta actualización documental se basa en la revisión del código y de la documentación disponibles. No añade métricas de ahorro, clientes, usuarios ni resultados de producción que no estén respaldados.

## Capacidad que demuestra

Separar rutas y servicios, mantener contexto por empresa y probar integraciones con un recorrido local.

[Volver al README](README.md).
