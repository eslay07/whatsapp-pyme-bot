# WhatsApp Pyme Bot

API comercial multiempresa que atiende clientes por WhatsApp, busca productos,
mantiene el contexto de la conversación, comparte datos de pago y avisa al
propietario cuando aparece una intención de compra. Incluye un simulador local
que funciona sin Meta ni una clave de inteligencia artificial.

## ¿Qué hace este sistema?

- Entiende consultas como `tienes alexa`, `tienes aleja` o `la tercera`.
- Busca únicamente dentro del catálogo de la empresa que recibió el mensaje.
- Muestra hasta tres opciones disponibles con precios reales.
- Conserva el historial por empresa y número de cliente.
- Ante una compra, registra un pedido pendiente y entrega los datos bancarios.
- Envía una alerta al propietario si WhatsApp está configurado.
- Permite usar OpenAI de forma opcional; si falla, continúa con el motor local.
- Evita procesar dos veces un mismo mensaje reenviado por Meta.

La aplicación no es un panel web visual. Es una API REST documentada
automáticamente en `/docs`, lista para conectarse a un panel o sistema existente.

## Arquitectura

```text
Cliente WhatsApp
       |
       v
Webhook FastAPI ---- firma Meta + idempotencia
       |
       v
Empresa identificada por phone_number_id
       |
       +---- historial de conversación
       +---- búsqueda difusa del catálogo
       +---- clasificador local / OpenAI opcional
       +---- pedido y datos de pago
       |
       v
WhatsApp Cloud API ---- respuesta al cliente / alerta al dueño
```

Cada producto, conversación y pedido lleva `empresa_id`. Las credenciales Meta
se guardan por empresa y el token se cifra antes de entrar en la base de datos.

## Requisitos previos

- Python 3.11 o 3.12.
- Git.
- Una terminal PowerShell, Bash o equivalente.
- Opcional: cuenta de Meta Developers para WhatsApp real.
- Opcional: cuenta de OpenAI si se desea mejorar la clasificación.
- Opcional: ngrok para exponer el servidor local.

En Windows, comprueba Python con:

```powershell
py --version
```

En Linux o macOS:

```bash
python3 --version
```

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/whatsapp-pyme-bot.git
cd whatsapp-pyme-bot
```

Si ya tienes estos archivos localmente, entra directamente en su directorio.

### 2. Crear entorno virtual

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Todas las dependencias están fijadas a versiones exactas para que el entorno
sea reproducible.

### 4. Configurar variables de entorno

Windows:

```powershell
Copy-Item .env.example .env
```

Linux o macOS:

```bash
cp .env.example .env
```

Para una prueba local gratuita basta con revisar estas variables:

```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./whatsapp_bot.db
ADMIN_SECRET_KEY=una-clave-larga-y-privada
ENCRYPTION_KEY=otra-clave-larga-y-estable
AI_PROVIDER=local
```

`ENCRYPTION_KEY` debe conservarse. Si cambia después de registrar tokens Meta,
estos ya no podrán descifrarse.

Variables disponibles:

| Variable | Uso |
|---|---|
| `DATABASE_URL` | SQLite local o PostgreSQL en despliegue |
| `ADMIN_SECRET_KEY` | Valor requerido en la cabecera `X-Admin-Key` |
| `ENCRYPTION_KEY` | Cifra los tokens Meta de cada empresa |
| `WHATSAPP_VERIFY_TOKEN` | Token elegido para el handshake del webhook |
| `META_APP_SECRET` | Valida la firma `X-Hub-Signature-256` |
| `WHATSAPP_API_VERSION` | Versión de Graph API usada para enviar mensajes |
| `AI_PROVIDER` | `local` u `openai` |
| `OPENAI_API_KEY` | Credencial opcional de OpenAI |
| `OPENAI_MODEL` | Modelo configurable, por defecto `gpt-5.4-mini` |
| `OPENAI_TIMEOUT_SECONDS` | Tiempo máximo antes del fallback local |

### 5. Crear la base de datos

El esquema se administra exclusivamente con Alembic:

```bash
alembic upgrade head
```

Para cargar una empresa demo y diez productos:

```bash
python datos_prueba.py
```

El script muestra el identificador de la empresa. Normalmente será `1`.

### 6. Iniciar el servidor

```bash
uvicorn app.main:app --reload
```

Abre:

- API: <http://127.0.0.1:8000>
- Documentación interactiva: <http://127.0.0.1:8000/docs>
- Estado: <http://127.0.0.1:8000/health>

### 7. Exponer con ngrok

Instala ngrok desde su sitio oficial y autentica tu cuenta. Con la API encendida:

```bash
ngrok http 8000
```

Ngrok mostrará una URL HTTPS semejante a:

```text
https://ejemplo-1234.ngrok-free.app
```

El webhook público será:

```text
https://ejemplo-1234.ngrok-free.app/webhook
```

La URL gratuita cambia al reiniciar ngrok; actualízala en Meta cuando ocurra.

### 8. Configurar el webhook en Meta

1. Crea una aplicación en Meta for Developers.
2. Agrega el producto WhatsApp.
3. En la configuración de webhooks usa la URL pública terminada en `/webhook`.
4. Usa exactamente el valor de `WHATSAPP_VERIFY_TOKEN` como token de verificación.
5. Suscribe el campo `messages`.
6. Copia el secreto de la aplicación a `META_APP_SECRET`.
7. Obtén el `phone_number_id` y un token apropiado.
8. Guarda ambos en la empresa mediante la API administrativa.

En producción, `META_APP_SECRET` es obligatorio. En `development`, si está vacío,
la firma se omite para facilitar pruebas manuales.

### 9. Agregar tu primera empresa

Todas las rutas `/admin` requieren `X-Admin-Key`.

```bash
curl -X POST http://127.0.0.1:8000/admin/empresas \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: una-clave-larga-y-privada" \
  -d '{
    "nombre": "Mi Tienda",
    "telefono_whatsapp": "+593999999999",
    "telefono_notificacion": "+593988888888",
    "numero_cuenta_banco": "2200123456",
    "nombre_banco": "Mi Banco",
    "nombre_titular_cuenta": "Mi Tienda S.A.",
    "mensaje_pago_personalizado": "Puedes pagar por transferencia:",
    "meta_phone_number_id": "ID_ENTREGADO_POR_META",
    "meta_access_token": "TOKEN_ENTREGADO_POR_META",
    "activa": true
  }'
```

La respuesta incluye `meta_configurada`, pero nunca devuelve el token.

### 10. Agregar productos

Sustituye `1` por el identificador de la empresa:

```bash
curl -X POST http://127.0.0.1:8000/admin/empresas/1/productos \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: una-clave-larga-y-privada" \
  -d '{
    "nombre": "Alexa Echo Dot 3ra Generación",
    "descripcion": "Altavoz inteligente compacto con asistente Alexa",
    "precio": "60.00",
    "stock": 10,
    "palabras_clave": "alexa,aleja,echo dot,amazon,3ra,tercera generación",
    "categoria": "Asistentes",
    "disponible": true
  }'
```

Los precios viajan como cadenas decimales en JSON para evitar errores de punto
flotante.

### 11. Probar con WhatsApp Simulator

En `/docs`, abre `POST /test/simular-mensaje`, pulsa **Try it out** y usa:

```json
{
  "empresa_id": 1,
  "numero_cliente": "+593999999999",
  "mensaje": "hola tienes aleja?"
}
```

No se requiere `X-Admin-Key`, Meta ni OpenAI. No uses este endpoint públicamente
en una instalación comercial sin añadir autenticación o bloquearlo por red.

## Cómo probar localmente sin Meta

Secuencia de ejemplo:

```bash
curl -X POST http://127.0.0.1:8000/test/simular-mensaje \
  -H "Content-Type: application/json" \
  -d '{"empresa_id":1,"numero_cliente":"+593999999999","mensaje":"tienes alexa?"}'
```

```bash
curl -X POST http://127.0.0.1:8000/test/simular-mensaje \
  -H "Content-Type: application/json" \
  -d '{"empresa_id":1,"numero_cliente":"+593999999999","mensaje":"la tercera"}'
```

```bash
curl -X POST http://127.0.0.1:8000/test/simular-mensaje \
  -H "Content-Type: application/json" \
  -d '{"empresa_id":1,"numero_cliente":"+593999999999","mensaje":"me la llevo, como pago?"}'
```

La respuesta contiene:

```json
{
  "respuesta_bot": "texto enviado al cliente",
  "intencion_detectada": "buscar_producto",
  "productos_encontrados": [],
  "modo_ia": "local"
}
```

Para ejecutar las pruebas automatizadas:

```bash
pytest --cov=app --cov-report=term-missing
```

## Activar OpenAI

Edita `.env`:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.4-mini
```

Reinicia el servidor. La integración usa Responses API y salida estructurada
validada por Pydantic. Antes de consultar al modelo, el servidor preselecciona
productos reales; cualquier identificador inexistente se descarta. Si hay un
timeout, error de red o respuesta inválida, el motor local responde sin detener
la conversación.

El uso de la API de OpenAI puede tener costo y no es necesario para desarrollar
o demostrar el sistema.

## Endpoints

| Método | Ruta | Protección | Descripción |
|---|---|---|---|
| GET | `/health` | Pública | Estado de API y base de datos |
| GET | `/webhook` | Token Meta | Handshake de verificación |
| POST | `/webhook` | Firma Meta | Mensajes entrantes |
| POST | `/test/simular-mensaje` | Pública | Simulación local |
| POST | `/admin/empresas` | Admin | Crear empresa |
| GET | `/admin/empresas/{id}` | Admin | Consultar empresa |
| PUT | `/admin/empresas/{id}` | Admin | Actualizar empresa |
| GET | `/admin/empresas/{id}/productos` | Admin | Listar catálogo |
| POST | `/admin/empresas/{id}/productos` | Admin | Crear producto |
| PUT | `/admin/productos/{id}` | Admin | Actualizar producto |
| DELETE | `/admin/productos/{id}` | Admin | Eliminar producto |
| GET | `/admin/conversaciones/{empresa_id}` | Admin | Consultar historiales |

## Cómo hacer deploy en Railway

Railway dispone actualmente de crédito gratuito limitado para experimentación;
no debe interpretarse como alojamiento comercial gratuito e ilimitado. Revisa
los precios vigentes antes de ofrecer un SLA.

1. Publica el proyecto en GitHub.
2. En Railway elige **New Project** y **Deploy from GitHub repo**.
3. Selecciona este repositorio.
4. Agrega un servicio PostgreSQL.
5. Copia su URL en `DATABASE_URL` si Railway no la inyecta automáticamente.
6. Configura todas las variables secretas de `.env.example`.
7. Usa como comando de inicio:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

8. Genera un dominio público.
9. Comprueba `https://TU_DOMINIO/health`.
10. Configura `https://TU_DOMINIO/webhook` en Meta.

No uses SQLite en Railway, Render u otro sistema con disco efímero: los datos
pueden desaparecer al reiniciar o desplegar. PostgreSQL evita ese problema.

## Alternativa en Render

El archivo `render.yaml` contiene una plantilla. En el panel de Render:

1. Crea un Blueprint desde el repositorio.
2. Asigna una base PostgreSQL y su URL.
3. Completa los secretos.
4. Despliega y comprueba `/health`.

Los servicios gratuitos pueden dormir tras inactividad y su disco local es
efímero. La base PostgreSQL gratuita también puede tener duración limitada.

## Cómo agregar una nueva empresa cliente

1. Crea una cuenta/número de WhatsApp Cloud API para el cliente.
2. Registra la empresa con su `meta_phone_number_id` y token.
3. Agrega su catálogo usando el `empresa_id` devuelto.
4. Prueba primero con `/test/simular-mensaje`.
5. Envía un mensaje real al número conectado.
6. Revisa el historial en `/admin/conversaciones/{empresa_id}`.
7. Rota el token mediante `PUT /admin/empresas/{id}` cuando sea necesario.

Los datos nunca se mezclan: la empresa se identifica desde el
`phone_number_id` presente en cada evento de Meta.

## Estructura de archivos explicada

```text
app/
  main.py                 Ensambla FastAPI y sus rutas
  config.py               Variables de entorno
  database.py             Motor y sesiones SQLAlchemy
  dependencies.py         Protección administrativa
  models/                 Empresas, productos, conversaciones y pedidos
  routes/                 Webhook, CRUD, salud y simulador
  services/               IA, catálogo, WhatsApp, cifrado y orquestación
  prompts/                Instrucciones versionadas de OpenAI
migrations/               Historial Alembic del esquema
tests/                    Pruebas unitarias y de integración
datos_prueba.py           Carga reproducible de demostración
render.yaml               Plantilla opcional para Render
Procfile                  Comando compatible con Railway/Render
```

## Seguridad y producción

Antes de vender el servicio:

- Usa secretos largos generados aleatoriamente.
- Configura `ENVIRONMENT=production` y `META_APP_SECRET`.
- Protege o desactiva el simulador público.
- Sustituye la clave administrativa por JWT con roles si habrá varios usuarios.
- Añade rate limiting delante de endpoints públicos.
- Usa PostgreSQL administrado con copias de seguridad.
- Registra errores y métricas sin guardar tokens ni datos bancarios completos.
- Define políticas de retención y eliminación del historial.
- Usa tokens Meta de larga duración y un procedimiento de rotación.
- Revisa las normas de consentimiento, plantillas y ventana de servicio de Meta.

## Integración continua

`.github/workflows/ci.yml` ejecuta en cada push a `main` y pull request:

1. instalación reproducible;
2. migración Alembic;
3. pruebas con cobertura.

## Preguntas frecuentes

### ¿Necesito pagar para probarlo?

No. `AI_PROVIDER=local` y `/test/simular-mensaje` permiten probar el flujo sin
Meta ni OpenAI.

### ¿Por qué no crea las tablas al arrancar?

Para que cada cambio de esquema sea explícito, auditable y compatible con
producción. Ejecuta `alembic upgrade head`.

### ¿Puedo usar PostgreSQL sin cambiar código?

Sí. Instala las dependencias y cambia `DATABASE_URL` por una URL PostgreSQL.

### ¿Qué ocurre si OpenAI falla?

La petición se clasifica con reglas locales y la conversación continúa.

### ¿Qué ocurre si Meta reenvía el mismo mensaje?

El identificador `wamid` queda registrado y el segundo evento se ignora.

### ¿Admite audios, imágenes o documentos?

Esta versión procesa solo texto. Los demás tipos se reconocen y se ignoran con
respuesta HTTP 200 para evitar reintentos innecesarios.

### ¿Por qué el token Meta no aparece al consultar la empresa?

Se cifra en reposo y se excluye deliberadamente de todos los esquemas públicos.

### ¿Puedo cambiar de modelo?

Sí, mediante `OPENAI_MODEL`. Verifica que el modelo soporte salida estructurada
en Responses API.

## Ejecución rápida en tres comandos

Después de crear y activar el entorno virtual:

```bash
pip install -r requirements.txt
alembic upgrade head && python datos_prueba.py
uvicorn app.main:app --reload
```

## Referencias

- [OpenAI Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api/)
- [Railway Pricing](https://docs.railway.com/pricing)
- [Render Free Services](https://render.com/docs/free)

