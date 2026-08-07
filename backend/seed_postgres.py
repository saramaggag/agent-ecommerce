import json
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="atlas_wear",
    user="postgres",
    password="sara2003"
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