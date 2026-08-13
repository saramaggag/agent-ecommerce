import re
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
    """Cherche dans les deux collections, retourne le(s) meilleur(s) résultat(s) si assez pertinent(s)."""
    res_p = produits_collection.query(query_texts=[question], n_results=5)
    res_f = faq_collection.query(query_texts=[question], n_results=3)

    dist_p = res_p["distances"][0][0]
    dist_f = res_f["distances"][0][0]

    if dist_p <= dist_f and dist_p < SEUIL_RAG:
        produits_pertinents = [
            doc for doc, dist in zip(res_p["documents"][0], res_p["distances"][0])
            if dist < SEUIL_RAG + 0.1
        ]
        contexte = "\n".join(produits_pertinents)
        return contexte, dist_p
    elif dist_f < SEUIL_RAG:
        faq_pertinentes = [
            doc for doc, dist in zip(res_f["documents"][0], res_f["distances"][0])
            if dist < SEUIL_RAG + 0.1
        ]
        contexte = "\n".join(faq_pertinentes)
        return contexte, dist_f
    else:
        return None, min(dist_p, dist_f)

# --- Outil 1 : consulter_stock ---
def consulter_stock(produit, taille=None, couleur=None):
    conn = get_connection()
    cur = conn.cursor()

    produit_propre = re.sub(r"\(.*?\)", "", produit)
    produit_propre = re.sub(r"[^\w\s-]", " ", produit_propre)
    mots = produit_propre.lower().split()
    mots_utiles = [m.rstrip("s") for m in mots if m not in ("le", "la", "les", "un", "une", "des", "de") and len(m) > 2]

    if not mots_utiles:
        conn.close()
        return 0

    conditions = ["LOWER(p.nom) LIKE %s"]
    params = [f"%{mots_utiles[0]}%"]

    if taille:
        conditions.append("UPPER(s.taille) = %s")
        params.append(taille.upper())
    if couleur:
        conditions.append("LOWER(s.couleur) = %s")
        params.append(couleur.lower())

    requete = f"""
        SELECT SUM(s.quantite)
        FROM stock s
        JOIN produits p ON p.id = s.produit_id
        WHERE {' AND '.join(conditions)}
    """
    cur.execute(requete, params)
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
            "description": "Vérifie la quantité disponible d'un produit, optionnellement pour une taille et/ou une couleur données",
            "parameters": {
                "type": "object",
                "properties": {
                    "produit": {"type": "string", "description": "UNIQUEMENT le type de vêtement en un mot simple, ex: jean, t-shirt, robe, jupe, pull, veste, chemise, short. Jamais de nom complet ni de parenthèses."},
                    "taille": {"type": "string", "description": "La taille si mentionnée par le client (XS, S, M, L, XL). Ne pas inventer si non précisée."},
                    "couleur": {"type": "string", "description": "La couleur si mentionnée par le client, ex: noir, bleu, rouge. Ne jamais mettre une couleur dans le champ taille."}
                },
                "required": ["produit"]
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
    contexte_rag, distance = rechercher_rag(question_client)
    print(f"[DEBUG] Recherche RAG : distance={distance:.3f} | contexte={'trouvé' if contexte_rag else 'aucun'}")

    system_content = (
        "Tu es l'assistant du service client d'Atlas Wear. "
        "RÈGLE IMPORTANTE : pour TOUTE question demandant une quantité, une disponibilité exacte, un stock précis, "
        "ou combinant un produit avec une taille et/ou une couleur, tu DOIS TOUJOURS appeler l'outil consulter_stock, "
        "même si des informations générales sur le produit sont déjà données ci-dessous. "
        "Ne réponds JAMAIS toi-même en texte à ce type de question, et n'écris JAMAIS le nom d'un outil ou un appel de fonction dans ta réponse en texte. "
        "Pour le statut d'une commande, utilise suivre_commande. "
        "Pour toute autre question que tu ne peux pas traiter avec certitude, utilise escalader_humain. "
        "Si la question du client contient PLUSIEURS demandes différentes (ex: un produit ET une question de livraison), "
        "appelle TOUS les outils nécessaires pour y répondre complètement, pas seulement le premier. "
    )

    if contexte_rag:
        system_content += (
            f"Voici des informations générales trouvées dans notre base de connaissances (descriptions, politiques) : \"{contexte_rag}\". "
            "Utilise ceci UNIQUEMENT pour des questions descriptives générales (ex: existence d'un produit, politique de retour), "
            "JAMAIS pour répondre à une question de quantité ou stock précis — dans ce cas, utilise toujours consulter_stock. "
        )

    system_content += (
        "N'invente JAMAIS de détails supplémentaires (délais, promesses, canaux de contact) absents du contexte ou du résultat d'outil. "
        "Réponds à CHAQUE partie de la question du client. Reste bref. "
        "RÈGLE ABSOLUE FINALE : ta réponse ne doit JAMAIS contenir les mots 'outil', 'fonction', 'consulter_stock', 'suivre_commande', ou toute mention de comment tu obtiens l'information — "
        "parle uniquement du résultat, jamais du mécanisme."
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": question_client}
    ]

    reponse = ollama.chat(model="qwen2.5:3b", messages=messages, tools=outils, options={"temperature": 0})

    if not reponse.message.tool_calls:
        if contexte_rag:
            return reponse.message.content
        else:
            print("[DEBUG] Aucun outil ET aucun contexte RAG -> escalade forcée par le code")
            return escalader_humain(f"Question hors périmètre : {question_client}")

    messages.append({"role": "assistant", "content": "", "tool_calls": reponse.message.tool_calls})

    for appel in reponse.message.tool_calls:
        nom_fonction = appel.function.name
        args = appel.function.arguments
        print(f"[DEBUG] Le LLM demande : {nom_fonction}({args})")

        fonction_reelle = fonctions_disponibles[nom_fonction]
        resultat = fonction_reelle(**args)
        print(f"[DEBUG] Résultat réel : {resultat}")

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