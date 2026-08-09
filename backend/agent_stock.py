import ollama
import psycopg2
import chromadb
from chromadb.utils import embedding_functions

# --- Connexion PostgreSQL ---
def get_connection():
    return psycopg2.connect(
        host="localhost", port=5432, dbname="atlas_wear",
        user="postgres", password="sara2003"
    )

# --- Connexion ChromaDB ---
ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text",
)
chroma_client = chromadb.PersistentClient(path="./chroma_data")
produits_collection = chroma_client.get_collection(name="produits", embedding_function=ollama_ef)
faq_collection = chroma_client.get_collection(name="faq", embedding_function=ollama_ef)

SEUIL_RAG = 0.32  # calibré avec calibrer_rag.py

def rechercher_rag(question):
    """Cherche dans les deux collections, retourne le meilleur résultat si assez pertinent."""
    res_p = produits_collection.query(query_texts=[question], n_results=1)
    res_f = faq_collection.query(query_texts=[question], n_results=1)

    dist_p = res_p["distances"][0][0]
    dist_f = res_f["distances"][0][0]

    if dist_p <= dist_f and dist_p < SEUIL_RAG:
        return res_p["documents"][0][0], dist_p
    elif dist_f < SEUIL_RAG:
        return res_f["documents"][0][0], dist_f
    else:
        return None, min(dist_p, dist_f)

# --- Outil 1 : consulter_stock ---
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

# --- Outil 2 : suivre_commande ---
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

# --- Outil 3 : escalader_humain ---
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
    # --- Étape 1 : RAG toujours actif (Option A) ---
    contexte_rag, distance = rechercher_rag(question_client)
    print(f"[DEBUG] Recherche RAG : distance={distance:.3f} | contexte={'trouvé' if contexte_rag else 'aucun'}")

    system_content = (
        "Tu es l'assistant du service client d'Atlas Wear. "
        "Pour toute question sur le stock/disponibilité, utilise consulter_stock. "
        "Pour toute question sur le statut d'une commande, utilise suivre_commande. "
        "Pour toute autre question que tu ne peux pas traiter avec certitude, utilise escalader_humain. "
    )

    if contexte_rag:
        system_content += (
            f"Voici une information pertinente trouvée dans notre base de connaissances : \"{contexte_rag}\". "
            "Si elle répond à la question, réponds directement en te basant STRICTEMENT dessus, sans appeler d'outil. "
        )

    system_content += (
        "N'invente JAMAIS de détails supplémentaires (délais, promesses, canaux de contact) absents du contexte ou du résultat d'outil. "
        "Reste bref : 1 à 2 phrases. Ne mentionne jamais les outils au client."
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": question_client}
    ]

    reponse = ollama.chat(model="qwen2.5:3b", messages=messages, tools=outils, options={"temperature": 0})

    # --- Filet de sécurité : si aucun outil ET aucun contexte RAG fiable -> escalade forcée ---
    if not reponse.message.tool_calls:
        if contexte_rag:
            # Le LLM a répondu directement en s'appuyant sur le RAG, comportement autorisé
            return reponse.message.content
        else:
            print("[DEBUG] Aucun outil ET aucun contexte RAG -> escalade forcée par le code")
            return escalader_humain(f"Question hors périmètre : {question_client}")

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
        "Comment retourner un article ?",
        "Est-ce que vous vendez aussi des chaussures de sport ?"
    ]
    for q in questions:
        print(f"\nClient : {q}")
        print(f"Agent  : {repondre(q)}")