import psycopg2

conn = psycopg2.connect(
    host="localhost", port=5432, dbname="atlas_wear",
    user="postgres", password="sara2030"
)
cur = conn.cursor()

# --- Clients fictifs ---
clients = [
    ("Sara Alaoui", "0612345678", "whatsapp"),
    ("Youssef Benali", "0623456789", "web"),
    ("Imane Chraibi", "0634567890", "instagram"),
]
for nom, tel, canal in clients:
    cur.execute(
        "INSERT INTO clients (nom, telephone, canal_prefere) VALUES (%s, %s, %s) RETURNING id",
        (nom, tel, canal)
    )

# --- Récupère les ids clients créés ---
cur.execute("SELECT id FROM clients ORDER BY id")
client_ids = [row[0] for row in cur.fetchall()]

# --- Commandes fictives avec statuts variés ---
commandes = [
    (client_ids[0], "expediee", 140.00),
    (client_ids[1], "en_attente", 75.00),
    (client_ids[2], "livree", 220.00),
]
commande_ids = []
for client_id, statut, montant in commandes:
    cur.execute(
        "INSERT INTO commandes (client_id, statut, montant) VALUES (%s, %s, %s) RETURNING id",
        (client_id, statut, montant)
    )
    commande_ids.append(cur.fetchone()[0])

# --- Quelques articles par commande ---
items = [
    (commande_ids[0], 2, 1, "M", "rouge"),   # commande 1 : 1 jean M rouge
    (commande_ids[1], 8, 1, "S", "noir"),    # commande 2 : 1 jupe S noire
    (commande_ids[2], 3, 1, "L", "bleu"),    # commande 3 : 1 robe L bleue
]
for commande_id, produit_id, quantite, taille, couleur in items:
    cur.execute(
        "INSERT INTO commande_items (commande_id, produit_id, quantite, taille, couleur) VALUES (%s, %s, %s, %s, %s)",
        (commande_id, produit_id, quantite, taille, couleur)
    )

conn.commit()

print("Clients créés :", client_ids)
print("Commandes créées (avec leurs ids) :", commande_ids)

cur.close()
conn.close()