import ollama
import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost", port=5432, dbname="atlas_wear",
        user="postgres", password="sara2003"
    )

def consulter_stock(produit, taille):
    conn = get_connection()
    cur = conn.cursor()
    produit_normalise = produit.lower().rstrip("s")
    cur.execute(
        """
        SELECT SUM(s.quantite)
        FROM stock s
        JOIN produits p ON p.id = s.produit_id
        WHERE LOWER(p.nom) LIKE %s AND UPPER(s.taille) = %s
        """,
        (f"%{produit_normalise}%", taille.upper())
    )
    resultat = cur.fetchone()
    cur.close()
    conn.close()
    return resultat[0] if resultat and resultat[0] is not None else 0

def suivre_commande(numero_commande):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT c.id, c.statut, c.date_creation, c.montant, cl.nom
        FROM commandes c
        JOIN clients cl ON cl.id = c.client_id
        WHERE c.id = %s
        """,
        (numero_commande,)
    )
    resultat = cur.fetchone()
    cur.close()
    conn.close()

    if resultat is None:
        return "Commande introuvable."

    id_cmd, statut, date_creation, montant, nom_client = resultat
    statuts_clairs = {
        "en_attente": "en attente de préparation, pas encore expédiée",
        "expediee": "déjà expédiée, en cours de livraison",
        "livree": "déjà livrée"
    }
    statut_clair = statuts_clairs.get(statut, statut)
    return f"Commande #{id_cmd} pour {nom_client} : {statut_clair}. Montant : {montant} MAD. Passée le {date_creation.strftime('%d/%m/%Y')}."

def escalader_humain(raison):
    with open("escalades.log", "a", encoding="utf-8") as f:
        f.write(f"[ESCALADE] Raison : {raison}\n")
    return "Demande transmise à un conseiller humain, qui reprendra contact rapidement."

outils = [
    {
        "type": "function",
        "function": {
            "name": "consulter_stock",
            "description": "Vérifie la quantité disponible d'un produit pour une taille donnée",
            "parameters": {
                "type": "object",
                "properties": {
                    "produit": {"type": "string", "description": "Le nom du produit, ex: jean"},
                    "taille": {"type": "string", "description": "La taille, ex: L"}
                },
                "required": ["produit", "taille"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suivre_commande",
            "description": "Donne le statut, le montant et la date d'une commande à partir de son numéro",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_commande": {"type": "integer", "description": "Le numéro de la commande, ex: 1"}
                },
                "required": ["numero_commande"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalader_humain",
            "description": "Transfère la conversation à un conseiller humain quand la question sort du périmètre",
            "parameters": {
                "type": "object",
                "properties": {
                    "raison": {"type": "string", "description": "Résumé court de pourquoi la question nécessite un humain"}
                },
                "required": ["raison"]
            }
        }
    }
]

fonctions_disponibles = {
    "consulter_stock": consulter_stock,
    "suivre_commande": suivre_commande,
    "escalader_humain": escalader_humain
}

def repondre(question_client):
    messages = [
        {"role": "system", "content": "Tu es l'assistant du service client d'Atlas Wear. Tu DOIS toujours répondre en appelant un des trois outils : consulter_stock pour le stock, suivre_commande pour une commande, escalader_humain pour tout le reste. Après le résultat de l'outil, réponds en 1 à 2 phrases naturelles, basées STRICTEMENT sur ce résultat. N'ajoute AUCUN mot vague non présent dans le résultat (pas de 'rapidement', 'bientôt', 'sous peu', pas de délais ou promesses inventés). Ne mentionne jamais les outils au client."},
        {"role": "user", "content": question_client}
    ]

    reponse = ollama.chat(model="qwen2.5:3b", messages=messages, tools=outils, options={"temperature": 0})

    # --- Filet de sécurité : si le LLM n'a demandé aucun outil, on force l'escalade nous-mêmes ---
    if not reponse.message.tool_calls:
        print("[DEBUG] Aucun outil demandé par le LLM -> escalade forcée par le code")
        resultat = escalader_humain(f"Question hors périmètre non traitée automatiquement : {question_client}")
        return resultat

    appel = reponse.message.tool_calls[0]
    nom_fonction = appel.function.name
    args = appel.function.arguments
    print(f"[DEBUG] Le LLM demande : {nom_fonction}({args})")

    fonction_reelle = fonctions_disponibles[nom_fonction]
    resultat = fonction_reelle(**args)
    print(f"[DEBUG] Résultat réel : {resultat}")

    messages.append({"role": "assistant", "content": "", "tool_calls": reponse.message.tool_calls})
    messages.append({"role": "tool", "content": str(resultat)})

    reponse_finale = ollama.chat(model="qwen2.5:3b", messages=messages, options={"temperature": 0})
    return reponse_finale.message.content

if __name__ == "__main__":
    questions = [
        "Il reste des jeans en L ?",
        "Où en est ma commande numéro 1 ?",
        "Est-ce que vous vendez aussi des chaussures de sport ?"
    ]
    for q in questions:
        print(f"\nClient : {q}")
        print(f"Agent  : {repondre(q)}")