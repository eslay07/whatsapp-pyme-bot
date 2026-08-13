"""Agrega proveedores alternativos de WhatsApp."""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_whatsapp_providers"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("empresas")}
    if "whatsapp_provider" not in existing:
        op.add_column(
            "empresas",
            sa.Column(
                "whatsapp_provider",
                sa.String(30),
                nullable=False,
                server_default="meta",
            ),
        )
    if "twilio_account_sid" not in existing:
        op.add_column("empresas", sa.Column("twilio_account_sid", sa.String(100)))
    if "twilio_auth_token_encrypted" not in existing:
        op.add_column("empresas", sa.Column("twilio_auth_token_encrypted", sa.Text()))
    if "twilio_from_number" not in existing:
        op.add_column("empresas", sa.Column("twilio_from_number", sa.String(50)))


def downgrade() -> None:
    op.drop_column("empresas", "twilio_from_number")
    op.drop_column("empresas", "twilio_auth_token_encrypted")
    op.drop_column("empresas", "twilio_account_sid")
    op.drop_column("empresas", "whatsapp_provider")
