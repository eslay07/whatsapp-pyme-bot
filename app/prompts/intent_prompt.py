"""Texto auxiliar para clasificación estructurada."""

INTENT_PROMPT = """
Analiza el último mensaje considerando el historial y los candidatos.
Devuelve una intención entre: buscar_producto, confirmar_compra, solicitar_pago,
saludo, fuera_de_tema o ambiguo. Los ids seleccionados deben existir en los
candidatos. La respuesta propuesta no puede alterar precios ni inventar datos.
""".strip()

