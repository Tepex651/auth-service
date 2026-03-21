"""default_values

Revision ID: 8414523ec327
Revises: d7f5e2ce86b2
Create Date: 2026-04-08 13:20:12.410396

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8414523ec327"
down_revision: Union[str, Sequence[str], None] = "d7f5e2ce86b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Part 1: Roles (idempotent)
    op.execute("""
        INSERT INTO roles (name, description)
        VALUES
            ('admin', 'Default admin role'),
            ('user', 'Default user role')
        ON CONFLICT (name) DO NOTHING;
    """)

    # Part 2: Default users (idempotent)
    op.execute("""
        DO $$
        DECLARE
            admin_id INT;
            user_id INT;
        BEGIN
            SELECT id INTO STRICT admin_id FROM roles WHERE name = 'admin';
            SELECT id INTO STRICT user_id FROM roles WHERE name = 'user';

            INSERT INTO users (
                id, email, username, hashed_password, role_id,
                mfa_enabled, active, email_confirmed, created_at
            )
            VALUES
                (
                    '2eed4de9-16a5-4ed8-baab-8aca7fa4978a',
                    'admin@test.com',
                    'admin',
                    '$2b$12$/A43QNdJCQMhJT0fCWHmYetZ0K.iZSptowvnvI0dSl.1cU2jOu4ea',
                    admin_id,
                    FALSE,
                    TRUE,
                    TRUE,
                    NOW()
                ),
                (
                    '2eed4de9-16a5-4ed8-baab-8aca7fa4978b',
                    'user@test.com',
                    'user',
                    '$2b$12$/A43QNdJCQMhJT0fCWHmYetZ0K.iZSptowvnvI0dSl.1cU2jOu4ea',
                    user_id,
                    FALSE,
                    TRUE,
                    TRUE,
                    NOW()
                )
            ON CONFLICT (email) DO NOTHING;

            RAISE NOTICE 'Bootstrap IAM completed!';
        END $$;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
