import chromadb
from chromadb.utils import embedding_functions

ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text",
)

client = chromadb.PersistentClient(path="./chroma_data")
produits_collection = client.get_collection(name="produits", embedding_function=ollama_ef)
faq_collection = client.get_collection(name="faq", embedding_function=ollama_ef)

questions_test = [
    "Vous avez un jean bleu ?",              # devrait bien matcher produits
    "Comment retourner un article ?",         # devrait bien matcher faq
    "Est-ce que vous vendez des chaussures ?", # ne devrait PAS bien matcher (hors catalogue)
    "Quel temps fait-il aujourd'hui ?"        # totalement hors sujet
]

for q in questions_test:
    print(f"\n=== Question : {q} ===")
    res_p = produits_collection.query(query_texts=[q], n_results=1)
    res_f = faq_collection.query(query_texts=[q], n_results=1)
    print(f"  Meilleur match produits : distance={res_p['distances'][0][0]:.3f} | {res_p['documents'][0][0][:60]}...")
    print(f"  Meilleur match faq      : distance={res_f['distances'][0][0]:.3f} | {res_f['documents'][0][0][:60]}...")