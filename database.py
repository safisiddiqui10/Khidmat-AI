from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
load_dotenv()

engine = create_engine(
    os.getenv("DATABASE_URL")
)


# DATABASE_URL = (
#     f"postgresql://{os.getenv('DB_USER')}:"
#     f"{os.getenv('DB_PASSWORD')}@"
#     f"{os.getenv('DB_HOST')}:"
#     f"{os.getenv('DB_PORT')}/"
#     f"{os.getenv('DB_NAME')}"
# )

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS beneficiaries (
            id SERIAL PRIMARY KEY,
            name TEXT,
            phone TEXT,
            location TEXT,
            need TEXT,
            family_members TEXT
        )
    """))
    conn.commit()


INSERT_BENEFICIARY = """
INSERT INTO beneficiaries
(name, phone, location, need, family_members)
VALUES (:name, :phone, :location, :need, :family_members)
RETURNING id
"""


UPDATE_BENEFICIARY = """
UPDATE beneficiaries
SET
    name = COALESCE(:name, name),
    phone = COALESCE(:phone, phone),
    location = COALESCE(:location, location),
    need = COALESCE(:need, need),
    family_members = COALESCE(:family_members, family_members)
WHERE id = :id
"""

def save_or_update_beneficiary(row_id, data):

    with engine.connect() as conn:

        if row_id is None:

            result = conn.execute(
                text(INSERT_BENEFICIARY),
                data
            )

            conn.commit()

            return result.fetchone()[0]

        else:

            conn.execute(
                text(UPDATE_BENEFICIARY),
                {
                    "id": row_id,
                    **data
                }
            )

            conn.commit()

            return row_id



def get_latest_data():

    with engine.connect() as conn:

        result = conn.execute(text("""
            SELECT * FROM beneficiaries
            ORDER BY id DESC
            LIMIT 5
        """))

        return [
            dict(row._mapping)
            for row in result.fetchall()
        ]