import json
import chromadb
from chromadb.utils import embedding_functions

embedding_fn = embedding_functions.DefaultEmbeddingFunction()

client = chromadb.PersistentClient(path="./chroma_data_prod")

# --- Collection PRODUITS ---
produits_collection = client.get_or_create_collection(name="produits", embedding_function=embedding_fn)

with open("../data/produits.json", encoding="utf-8") as f:
    produits = json.load(f)

docs, ids, metadatas = [], [], []
for p in produits:
    texte = f"{p['nom']} ({p['categorie']}) - {p['description']} Prix: {p['prix']} MAD. Couleurs: {', '.join(p['couleurs'])}. Tailles: {', '.join(p['tailles'])}."
    docs.append(texte)
    ids.append(f"produit_{p['id']}")
    metadatas.append({"nom": p["nom"], "categorie": p["categorie"], "prix": p["prix"]})

produits_collection.add(documents=docs, ids=ids, metadatas=metadatas)
print(f"{len(docs)} produits ajoutés (embedding par défaut, prod).")

# --- Collection FAQ ---
faq_collection = client.get_or_create_collection(name="faq", embedding_function=embedding_fn)

with open("../data/faq.json", encoding="utf-8") as f:
    faqs = json.load(f)

docs, ids, metadatas = [], [], []
for i, item in enumerate(faqs):
    texte = f"Question: {item['question']} Réponse: {item['reponse']}"
    docs.append(texte)
    ids.append(f"faq_{i}")
    metadatas.append({"categorie": item["categorie"]})

faq_collection.add(documents=docs, ids=ids, metadatas=metadatas)
print(f"{len(docs)} FAQ ajoutées (embedding par défaut, prod).")

print("Ingestion de production terminée.")