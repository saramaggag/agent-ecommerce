import ollama
import psycopg2

# --- Connexion à PostgreSQL ---
def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="atlas_wear",
        user="postgres",
        password="sara2003"
    )

# --- La vraie fonction, celle qui exécute réellement ---
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
    quantite = resultat[0] if resultat and resultat[0] is not None else 0
    return quantite

# --- Description de l'outil pour le LLM ---
consulter_stock_tool = {
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
}

def repondre(question_client):
    messages = [
        {"role": "system", "content": "Tu es l'assistant du service client d'Atlas Wear, une boutique de vêtements marocaine. Réponds toujours de façon naturelle et chaleureuse, comme un vrai conseiller humain. Pour toute question sur la disponibilité, le stock ou une taille précise d'un produit, utilise obligatoirement l'outil consulter_stock pour obtenir l'information exacte avant de répondre. Ne mentionne JAMAIS les outils, les fonctions, ou ta façon de travailler en interne — le client ne doit voir qu'une réponse simple et directe, comme s'il parlait à une vraie personne."},
        {"role": "user", "content": question_client}
    ]

    # --- 1er appel : le LLM décide ---
    reponse = ollama.chat(model="qwen2.5:3b", messages=messages, tools=[consulter_stock_tool])

    if reponse.message.tool_calls:
        appel = reponse.message.tool_calls[0]
        args = appel.function.arguments
        print(f"[DEBUG] Le LLM demande : {appel.function.name}({args})")

        # --- Exécution réelle par notre code ---
        quantite = consulter_stock(args["produit"], args["taille"])
        print(f"[DEBUG] Résultat SQL réel : {quantite}")

        # --- On ajoute la proposition du LLM + le résultat à l'historique ---
        messages.append({"role": "assistant", "content": "", "tool_calls": reponse.message.tool_calls})
        messages.append({"role": "tool", "content": str(quantite)})

        # --- 2e appel : le LLM formule la réponse finale ---
        reponse_finale = ollama.chat(model="qwen2.5:3b", messages=messages)
        return reponse_finale.message.content
    else:
        return reponse.message.content

# --- Test ---
if __name__ == "__main__":
    question = "Il reste des jeans en L ?"
    print(f"Client : {question}")
    print(f"Agent  : {repondre(question)}")