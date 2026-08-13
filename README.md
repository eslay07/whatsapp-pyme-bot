# WhatsApp PyME Bot

Backend multiempresa para atención comercial por WhatsApp.

El proyecto recibe mensajes desde WhatsApp Cloud API, identifica a qué empresa pertenece el número que recibió la conversación, busca productos dentro de su catálogo y mantiene el contexto de cada cliente. Cuando detecta una intención de compra puede registrar el pedido, compartir instrucciones de pago y avisar al responsable de la empresa.

La inteligencia artificial es opcional. El sistema incluye un motor local para poder desarrollar, probar y demostrar el flujo sin depender de una API externa.

## Qué problema busca resolver

En una PyME es común que las mismas preguntas se repitan durante el día:

- si un producto está disponible;
- cuánto cuesta;
- cuál de varias opciones corresponde a lo que busca el cliente;
- cómo puede pagar;
- qué datos necesita para completar una compra.

Cuando todo esto se responde manualmente, el tiempo de atención crece junto con el número de conversaciones.

Este proyecto automatiza la primera parte de esa atención sin perder de vista algo importante: el bot solo trabaja con el catálogo y la configuración de la empresa que recibió el mensaje.

## Flujo general

```text
Cliente
   │
   ▼
WhatsApp Cloud API
   │
   ▼
Webhook FastAPI
   │
   ├── valida el evento
   ├── evita procesar duplicados
   └── identifica la empresa
          │
          ▼
   Servicio de conversación
          │
          ├── historial del cliente
          ├── búsqueda de catálogo
          ├── intención del mensaje
          ├── IA opcional
          └── pedido / pago
          │
          ▼
WhatsApp Cloud API
   │
   ├── respuesta al cliente
   └── aviso al responsable
```

## Características principales

- arquitectura multiempresa;
- integración con WhatsApp Cloud API;
- webhook de verificación y recepción de mensajes;
- validación de firma de Meta en producción;
- control de mensajes duplicados;
- catálogo independiente por empresa;
- búsqueda aproximada con tolerancia a errores de escritura;
- historial por empresa y número de cliente;
- registro de pedidos;
- información de pago configurable por empresa;
- aviso al responsable cuando aparece intención de compra;
- motor local de clasificación;
- integración opcional con OpenAI;
- fallback automático al motor local;
- API administrativa;
- cifrado de tokens de Meta;
- SQLite para desarrollo;
- PostgreSQL para despliegue;
- migraciones con Alembic;
- simulador local sin Meta;
- documentación automática de FastAPI;
- pruebas automatizadas.

## Ejemplo sencillo

Un cliente podría escribir:

```text
hola tienes aleja?
```

Aunque escribió `aleja` en lugar de `alexa`, el buscador puede encontrar productos relacionados dentro del catálogo correspondiente.

Después el cliente puede continuar:

```text
la tercera
```

El sistema conserva el contexto de la conversación y puede relacionar esa frase con las opciones mostradas anteriormente.

Finalmente:

```text
me la llevo, como pago?
```

Ese mensaje puede llevar el flujo hacia una intención de compra, creación del pedido e instrucciones de pago.

## Arquitectura del proyecto

La aplicación está construida con FastAPI y separa las rutas HTTP de la lógica de negocio.

```text
app/
│
├── main.py
├── config.py
├── database.py
├── dependencies.py
├── schemas.py
│
├── models/
│
├── routes/
│   ├── admin.py
│   ├── health.py
│   ├── test_simulator.py
│   └── webhook.py
│
├── services/
│   ├── ai_service.py
│   ├── catalogo_service.py
│   ├── conversation_service.py
│   ├── notificacion_service.py
│   ├── security_service.py
│   └── whatsapp_service.py
│
└── prompts/
```

Fuera de `app/` se mantienen las migraciones, pruebas y archivos de despliegue:

```text
migrations/
tests/
alembic.ini
datos_prueba.py
requirements.txt
render.yaml
Procfile
.env.example
```

## Separación por responsabilidades

### Rutas

`app/routes/` recibe las solicitudes HTTP.

Actualmente contiene:

- `webhook.py`: comunicación entrante desde Meta;
- `admin.py`: administración de empresas, productos y conversaciones;
- `health.py`: comprobación del estado de la aplicación;
- `test_simulator.py`: simulación local de mensajes.

### Servicios

`app/services/` contiene la lógica que no debería vivir directamente dentro de una ruta.

Entre los servicios actuales están:

- catálogo;
- conversación;
- IA;
- WhatsApp;
- notificaciones;
- seguridad y cifrado.

Esta separación ayuda a probar cada parte sin tener que levantar siempre todo el servidor.

## Multiempresa

La empresa se identifica a partir del `phone_number_id` recibido desde Meta.

Los registros de negocio se relacionan con una empresa concreta. Eso incluye, entre otros:

- productos;
- conversaciones;
- pedidos;
- configuración de WhatsApp.

La intención es evitar que el catálogo o el historial de una empresa aparezca accidentalmente en la conversación de otra.

## Catálogo y búsqueda

El catálogo se guarda en la base de datos y cada producto pertenece a una empresa.

La búsqueda no depende únicamente de coincidencias exactas. El proyecto utiliza `rapidfuzz` para tolerar consultas aproximadas o errores comunes de escritura.

Esto permite resolver búsquedas como:

```text
alexa
aleja
echo
echo dot
tercera generacion
```

sin exigir que el cliente escriba exactamente el nombre almacenado en la base.

## Conversaciones

Cada conversación conserva contexto por:

```text
empresa + número de cliente
```

Esto permite que una respuesta corta tenga sentido después de una pregunta anterior.

Ejemplo:

```text
Cliente: tienes alexa?
Bot: ...
Cliente: la tercera
```

La segunda frase se interpreta usando el historial reciente y no como un mensaje completamente independiente.

## Inteligencia artificial

El proyecto puede trabajar de dos maneras:

```text
AI_PROVIDER=local
```

o:

```text
AI_PROVIDER=openai
```

El modo local permite ejecutar el sistema sin una clave externa.

Si se configura OpenAI, el servicio puede utilizarlo como apoyo para interpretar la intención del mensaje. Antes de enviar información al modelo se trabaja con productos candidatos reales del catálogo.

Si la llamada externa falla, excede el tiempo configurado o devuelve una respuesta inválida, el flujo puede continuar con el motor local.

La IA es una ayuda para interpretación; el catálogo y los identificadores válidos siguen viniendo de la base de datos.

## Seguridad

Los tokens de Meta no se devuelven desde la API administrativa y se cifran antes de almacenarse.

La configuración sensible debe estar en `.env`, nunca dentro del código.

El repositorio publica únicamente:

```text
.env.example
```

como referencia de las variables necesarias.

Entre las variables utilizadas están:

```text
ENVIRONMENT
DATABASE_URL
ADMIN_SECRET_KEY
ENCRYPTION_KEY
WHATSAPP_VERIFY_TOKEN
META_APP_SECRET
WHATSAPP_API_VERSION
AI_PROVIDER
OPENAI_API_KEY
OPENAI_MODEL
OPENAI_TIMEOUT_SECONDS
```

`ENCRYPTION_KEY` debe mantenerse estable. Si se cambia después de haber cifrado tokens, las credenciales guardadas anteriormente ya no podrán recuperarse correctamente.

## Requisitos

- Python 3.11 o 3.12;
- Git;
- pip;
- opcionalmente una cuenta de Meta Developers;
- opcionalmente una clave de OpenAI;
- PostgreSQL para una instalación persistente en servidor.

## Instalación en Windows

### 1. Entrar al proyecto

```cmd
cd /d "RUTA\whatsapp-pyme-bot"
```

### 2. Crear el entorno virtual

```cmd
py -3.12 -m venv .venv
```

### 3. Activarlo desde CMD

```cmd
.venv\Scripts\activate.bat
```

### 4. Instalar dependencias

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Crear la configuración local

```cmd
copy .env.example .env
```

Edita `.env` y cambia como mínimo las claves locales.

Para desarrollo sin Meta ni OpenAI:

```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./whatsapp_bot.db
ADMIN_SECRET_KEY=CAMBIA_ESTA_CLAVE
ENCRYPTION_KEY=CAMBIA_ESTA_CLAVE
AI_PROVIDER=local
```

## Base de datos

El esquema se administra con Alembic.

Después de instalar las dependencias:

```cmd
alembic upgrade head
```

Para cargar información de demostración:

```cmd
python datos_prueba.py
```

La base local de desarrollo puede ser SQLite.

En despliegues con almacenamiento efímero conviene utilizar PostgreSQL.

## Iniciar la API

```cmd
uvicorn app.main:app --reload
```

Con la configuración local habitual estarán disponibles:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health
```

`/docs` abre la documentación interactiva generada por FastAPI.

## Simulador local

El simulador permite probar la lógica sin configurar todavía un número real de WhatsApp.

Ruta:

```text
POST /test/simular-mensaje
```

Ejemplo:

```json
{
  "empresa_id": 1,
  "numero_cliente": "+593999999999",
  "mensaje": "hola tienes aleja?"
}
```

El simulador es muy útil durante desarrollo, pero una instalación pública debería protegerlo o deshabilitarlo si no se necesita.

## API administrativa

Las rutas administrativas utilizan:

```text
X-Admin-Key
```

como protección básica.

La clave debe coincidir con:

```text
ADMIN_SECRET_KEY
```

Entre las operaciones disponibles están:

- crear y actualizar empresas;
- consultar empresas;
- administrar productos;
- consultar conversaciones.

Esta protección es suficiente para el alcance actual del proyecto, pero si se construye un panel multiusuario debería evolucionar hacia autenticación y autorización con roles.

## Webhook de Meta

El webhook utiliza:

```text
GET /webhook
```

para el proceso de verificación y:

```text
POST /webhook
```

para recibir eventos.

En producción debe configurarse:

```text
META_APP_SECRET
```

para validar la firma enviada por Meta.

El proyecto también evita procesar más de una vez el mismo mensaje cuando Meta reintenta la entrega.

## Envío de mensajes

La comunicación saliente está encapsulada en el servicio de WhatsApp.

Cada empresa puede tener su propia configuración de Meta.

Esto permite que la lógica general de atención se reutilice sin mezclar tokens o números entre negocios.

## Datos de pago

Cada empresa puede mantener su propia información de pago.

Cuando se identifica una compra, el bot puede devolver esos datos al cliente de acuerdo con la configuración almacenada.

Los ejemplos y datos de demostración no deben contener cuentas bancarias reales.

## Pruebas

El proyecto tiene pruebas separadas para varias áreas:

```text
tests/test_admin.py
tests/test_ai_service.py
tests/test_catalogo.py
tests/test_migrations.py
tests/test_simulator.py
tests/test_webhook.py
```

Para ejecutarlas:

```cmd
py -3.12 -m pytest
```

Con cobertura:

```cmd
py -3.12 -m pytest --cov=app --cov-report=term-missing
```

Esta validación debería ejecutarse antes de confirmar cambios importantes.

## Dependencias principales

El proyecto utiliza, entre otras:

- FastAPI;
- SQLAlchemy;
- Alembic;
- Pydantic;
- psycopg;
- httpx;
- cryptography;
- RapidFuzz;
- OpenAI;
- pytest;
- Uvicorn.

Las versiones exactas están fijadas en `requirements.txt`.

## Despliegue

El repositorio contiene:

```text
render.yaml
Procfile
```

para facilitar el despliegue.

La aplicación necesita ejecutar las migraciones antes de iniciar el servidor.

Un comando de inicio habitual es:

```text
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

En producción se recomienda PostgreSQL y no una base SQLite dentro de un disco efímero.

## Integración continua

El repositorio incluye configuración bajo:

```text
.github/
```

para automatizar comprobaciones del proyecto.

Antes de aceptar un cambio importante deberían pasar:

- instalación de dependencias;
- migraciones;
- pruebas automatizadas.

## Qué no debe publicarse

No deben entrar al repositorio:

- `.env`;
- bases SQLite locales;
- credenciales;
- tokens Meta;
- claves OpenAI;
- claves de cifrado;
- logs con conversaciones reales;
- datos bancarios reales;
- exports con información de clientes;
- archivos de IDE;
- entornos virtuales;
- notas personales de Git.

`.env.example` sí debe mantenerse porque contiene solamente nombres de variables y valores de demostración.

## Comentarios en el código

Los comentarios deberían explicar decisiones que no son obvias.

Ejemplo útil:

```python
# Meta puede reenviar el mismo evento si no recibe respuesta a tiempo.
# Guardamos el identificador para evitar responder dos veces al cliente.
```

Otro ejemplo:

```python
# La búsqueda siempre se limita a la empresa actual.
# Un resultado de otra empresa nunca debe participar como candidato.
```

No hace falta comentar instrucciones evidentes como:

```python
# Devuelve el resultado
return resultado
```

La intención es que los comentarios ayuden a entender el motivo de una regla, no que traduzcan Python al español línea por línea.

## Flujo recomendado para cambios

```text
1. Actualizar la rama local.
2. Modificar una parte concreta.
3. Ejecutar las pruebas.
4. Revisar los cambios.
5. Preparar únicamente los archivos relacionados.
6. Crear un commit descriptivo.
7. Publicar.
```

## Estado de ramas

La rama pública principal es:

```text
main
```

La variante de interfaz de escritorio debe revisarse por separado antes de publicarse, para confirmar que siga teniendo sentido como alternativa y no como parte de la API principal.

## Autor

**Jimmy Omar Toapanta Guayanay**  
Ingeniero en Informática — Quito, Ecuador
