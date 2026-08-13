"""Carga una empresa y diez productos tecnológicos para demostración."""

from decimal import Decimal

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Empresa, Producto

PRODUCTOS = [
    ("Alexa Echo Dot 3ra Generación", "Altavoz inteligente compacto con Alexa.", "60.00", 12, "alexa,aleja,echo dot,amazon,3ra,tercera generacion", "Asistentes"),
    ("Alexa Echo Dot 5ta Generación", "Altavoz inteligente con mejor sonido y sensor de temperatura.", "89.90", 8, "alexa,echo dot,amazon,5ta,quinta generacion", "Asistentes"),
    ("Google Nest Mini 2da Generación", "Asistente de voz compacto con Google Assistant.", "55.00", 7, "google home,nest,asistente,2da,segunda", "Asistentes"),
    ("Audífonos Bluetooth Pro", "Audífonos inalámbricos con cancelación de ruido.", "39.99", 20, "audifonos,auriculares,bluetooth,inalambricos", "Audio"),
    ("Smartwatch Fit X2", "Reloj inteligente con medición deportiva y notificaciones.", "49.50", 15, "reloj,smart watch,deporte,fitness", "Wearables"),
    ("Cámara WiFi 360", "Cámara de seguridad con visión nocturna y audio bidireccional.", "42.00", 10, "camara,seguridad,wifi,vigilancia,360", "Seguridad"),
    ("Teclado Mecánico RGB", "Teclado compacto con switches mecánicos e iluminación RGB.", "67.00", 9, "teclado,gamer,mecanico,rgb", "Computación"),
    ("Mouse Inalámbrico Ergo", "Mouse ergonómico recargable de seis botones.", "24.90", 25, "mouse,raton,inalambrico,ergonomico", "Computación"),
    ("Cargador USB-C 65W", "Cargador rápido compatible con teléfonos y laptops.", "34.00", 30, "cargador,tipo c,usb c,rapido,65w", "Accesorios"),
    ("Power Bank 20000 mAh", "Batería portátil con carga rápida y dos puertos USB.", "38.50", 18, "bateria,portatil,powerbank,20000,carga", "Accesorios"),
]


def main() -> None:
    """Inserta datos solo si la empresa de ejemplo aún no existe."""
    with SessionLocal() as db:
        empresa = db.scalar(
            select(Empresa).where(Empresa.nombre == "Tecno Pyme Demo")
        )
        if empresa:
            print(f"Los datos ya existen. Empresa ID: {empresa.id}")
            return
        empresa = Empresa(
            nombre="Tecno Pyme Demo",
            telefono_whatsapp="+593 00 000 0000",
            telefono_notificacion="+593 00 000 0000",
            numero_cuenta_banco="2200123456",
            nombre_banco="Banco Demo",
            nombre_titular_cuenta="Tecno Pyme Demo S.A.",
            mensaje_pago_personalizado="¡Excelente elección! Paga mediante transferencia:",
            activa=True,
        )
        db.add(empresa)
        db.flush()
        for nombre, descripcion, precio, stock, palabras, categoria in PRODUCTOS:
            db.add(
                Producto(
                    empresa_id=empresa.id,
                    nombre=nombre,
                    descripcion=descripcion,
                    precio=Decimal(precio),
                    stock=stock,
                    palabras_clave=palabras,
                    categoria=categoria,
                    disponible=True,
                )
            )
        db.commit()
        print(f"Empresa {empresa.id} y 10 productos creados correctamente.")


if __name__ == "__main__":
    main()

