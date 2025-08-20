"""Add client_id to document_metadata

Revision ID: 002_add_client_id
Revises: 001_initial
Create Date: 2025-07-28 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "002_add_client_id"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add client_id column to document_metadata table
    op.add_column(
        "document_metadata",
        sa.Column("client_id", sa.String(), nullable=False, server_default="default"),
    )

    # Create index on client_id for better query performance
    op.create_index(
        "idx_document_metadata_client_id", "document_metadata", ["client_id"]
    )

    # Remove the default value after adding the column
    op.alter_column("document_metadata", "client_id", server_default=None)


def downgrade() -> None:
    # Drop the index
    op.drop_index("idx_document_metadata_client_id", table_name="document_metadata")

    # Drop the client_id column
    op.drop_column("document_metadata", "client_id")
