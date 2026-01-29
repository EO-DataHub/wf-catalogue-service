"""seed_default_catalogue.

Revision ID: def5cf9aedc9
Revises: c0c07ddc40ed
Create Date: 2026-01-22 13:26:36.608567

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "def5cf9aedc9"
down_revision: str | Sequence[str] | None = "c0c07ddc40ed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_CATALOGUE_ID = "eodh-workflows-notebooks"


def upgrade() -> None:
    """Seed default catalogue matching workflow-catalogue repo."""
    # Insert default catalogue
    op.execute(f"""
        INSERT INTO catalogues (id, type, item_type, title, description, keywords, language, created, updated, license, conforms_to)
        VALUES (
            '{DEFAULT_CATALOGUE_ID}',
            'Collection',
            'record',
            'EODH Workflows and Notebooks Catalog',
            'A catalog of Earth observation data processing workflows and interactive notebooks available for various collections. This catalog provides discoverable metadata for workflows and notebooks that can be executed against STAC collections.',
            ARRAY['workflows', 'notebooks', 'earth observation', 'processing', 'analysis', 'sentinel', 'ndvi', 'jupyter'],
            'en',
            '2024-10-14T00:00:00Z',
            '2024-10-14T00:00:00Z',
            'proprietary',
            ARRAY['http://www.opengis.net/doc/IS/ogcapi-records-1/1.0']
        )
        ON CONFLICT (id) DO NOTHING
    """)

    # Insert theme
    op.execute(f"""
        INSERT INTO themes (catalogue_id, scheme)
        VALUES ('{DEFAULT_CATALOGUE_ID}', 'https://example.org/eodh/themes')
    """)

    # Insert concepts (get theme_id dynamically)
    op.execute(f"""
        INSERT INTO concepts (theme_id, concept_id, title)
        SELECT id, 'earth-observation', 'Earth Observation'
        FROM themes WHERE catalogue_id = '{DEFAULT_CATALOGUE_ID}'
    """)
    op.execute(f"""
        INSERT INTO concepts (theme_id, concept_id, title)
        SELECT id, 'data-processing', 'Data Processing'
        FROM themes WHERE catalogue_id = '{DEFAULT_CATALOGUE_ID}'
    """)
    op.execute(f"""
        INSERT INTO concepts (theme_id, concept_id, title)
        SELECT id, 'remote-sensing', 'Remote Sensing'
        FROM themes WHERE catalogue_id = '{DEFAULT_CATALOGUE_ID}'
    """)

    # Insert contact
    op.execute(f"""
        INSERT INTO contacts (id, entity_id, entity_type, name, organization, roles)
        VALUES (
            'eodh-platform-contact',
            '{DEFAULT_CATALOGUE_ID}',
            'catalogue',
            'EODH Platform',
            NULL,
            ARRAY['publisher']
        )
    """)


def downgrade() -> None:
    """Remove default catalogue and related data."""
    op.execute(f"DELETE FROM contacts WHERE entity_id = '{DEFAULT_CATALOGUE_ID}'")
    op.execute(f"DELETE FROM themes WHERE catalogue_id = '{DEFAULT_CATALOGUE_ID}'")
    op.execute(f"DELETE FROM catalogues WHERE id = '{DEFAULT_CATALOGUE_ID}'")
