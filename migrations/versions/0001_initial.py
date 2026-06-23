"""Esquema inicial multiempresa."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "empresas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("telefono_whatsapp", sa.String(30), nullable=False),
        sa.Column("telefono_notificacion", sa.String(30), nullable=False),
        sa.Column("numero_cuenta_banco", sa.String(100), nullable=False),
        sa.Column("nombre_banco", sa.String(100), nullable=False),
        sa.Column("nombre_titular_cuenta", sa.String(150), nullable=False),
        sa.Column("mensaje_pago_personalizado", sa.Text()),
        sa.Column("meta_phone_number_id", sa.String(100), unique=True),
        sa.Column("meta_access_token_encrypted", sa.Text()),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_empresas_meta_phone_number_id",
        "empresas",
        ["meta_phone_number_id"],
        unique=True,
    )
    op.create_table(
        "productos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("empresa_id", sa.Integer(), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("precio", sa.Numeric(12, 2), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("palabras_clave", sa.Text(), nullable=False),
        sa.Column("categoria", sa.String(100), nullable=False),
        sa.Column("disponible", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_productos_empresa_id", "productos", ["empresa_id"])
    op.create_index("ix_productos_categoria", "productos", ["categoria"])
    op.create_table(
        "conversaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("empresa_id", sa.Integer(), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("numero_cliente", sa.String(30), nullable=False),
        sa.Column("historial_json", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("empresa_id", "numero_cliente", name="uq_conversacion_empresa_cliente"),
    )
    op.create_index("ix_conversaciones_empresa_id", "conversaciones", ["empresa_id"])
    op.create_index("ix_conversaciones_numero_cliente", "conversaciones", ["numero_cliente"])
    op.create_table(
        "pedidos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("empresa_id", sa.Integer(), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("numero_cliente", sa.String(30), nullable=False),
        sa.Column("productos_json", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_pedidos_empresa_id", "pedidos", ["empresa_id"])
    op.create_index("ix_pedidos_numero_cliente", "pedidos", ["numero_cliente"])
    op.create_index("ix_pedidos_estado", "pedidos", ["estado"])
    op.create_table(
        "mensajes_procesados",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("empresa_id", sa.Integer(), sa.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("whatsapp_message_id", sa.String(150), nullable=False, unique=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mensajes_procesados_empresa_id", "mensajes_procesados", ["empresa_id"])
    op.create_index("ix_mensajes_procesados_whatsapp_message_id", "mensajes_procesados", ["whatsapp_message_id"], unique=True)


def downgrade() -> None:
    op.drop_table("mensajes_procesados")
    op.drop_table("pedidos")
    op.drop_table("conversaciones")
    op.drop_table("productos")
    op.drop_table("empresas")
