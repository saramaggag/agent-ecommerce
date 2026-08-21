import chromadb
from chromadb.utils import embedding_functions

embedding_fn = embedding_functions.DefaultEmbeddingFunction()
client = chromadb.PersistentClient(path="./chroma_data_prod")
produits_collection = client.get_collection(name="produits", embedding_function=embedding_fn)
faq_collection = client.get_collection(name="faq", embedding_function=embedding_fn)

questions_test = [
    "Vous avez un jean bleu ?",
    "Comment retourner un article ?",
    "Est-ce que vous vendez des chaussures ?",
    "Quel temps fait-il aujourd'hui ?"
]

for q in questions_test:
    print(f"\n=== Question : {q} ===")
    res_p = produits_collection.query(query_texts=[q], n_results=1)
    res_f = faq_collection.query(query_texts=[q], n_results=1)
    print(f"  produits : distance={res_p['distances'][0][0]:.3f}")
    print(f"  faq      : distance={res_f['distances'][0][0]:.3f}")