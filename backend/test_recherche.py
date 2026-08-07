import chromadb

client = chromadb.PersistentClient(path="./chroma_data")

produits_collection = client.get_collection(name="produits")
faq_collection = client.get_collection(name="faq")

# Test 1 : question sur un produit
print("=== Question produit ===")
resultat = produits_collection.query(
    query_texts=["Vous avez un jean bleu ?"],
    n_results=2
)
for doc in resultat["documents"][0]:
    print("-", doc)

# Test 2 : question sur la FAQ
print("\n=== Question FAQ ===")
resultat = faq_collection.query(
    query_texts=["Comment je peux retourner un article ?"],
    n_results=2
)
for doc in resultat["documents"][0]:
    print("-", doc)