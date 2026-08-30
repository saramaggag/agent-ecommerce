import os
import json
import psycopg2
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=5432,
    dbname=os.getenv("DB_NAME", "atlas_wear"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD"),
    sslmode=os.getenv("DB_SSLMODE", "prefer")
)
cur = conn.cursor()

with open("../data/produits.json", encoding="utf-8") as f:
    produits = json.load(f)

for p in produits:
    cur.execute(
        """
        INSERT INTO produits (id, nom, categorie, prix, description)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        (p["id"], p["nom"], p["categorie"], p["prix"], p["description"])
    )

    couleur_principale = p["couleurs"][0]
    for taille, quantite in p["stock_par_variante"].items():
        cur.execute(
            """
            INSERT INTO stock (produit_id, taille, couleur, quantite)
            VALUES (%s, %s, %s, %s)
            """,
            (p["id"], taille, couleur_principale, quantite)
        )

conn.commit()
print(f"{len(produits)} produits et leur stock insérés dans PostgreSQL.")

cur.close()
conn.close()