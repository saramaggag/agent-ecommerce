import ollama

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

reponse = ollama.chat(
    model="qwen2.5:3b",
    messages=[
        {"role": "system", "content": "Tu es l'assistant d'Atlas Wear. RÈGLE STRICTE : pour toute question sur la disponibilité, le stock ou une taille précise d'un produit, tu DOIS obligatoirement utiliser l'outil consulter_stock. Ne réponds JAMAIS en texte libre à ce type de question, appelle toujours l'outil."},
        {"role": "user", "content": "Il reste des jeans en L ?"}
    ],
    tools=[consulter_stock_tool]
)

print("=== Réponse brute d'Ollama ===")
print(reponse.message)
print()
print("=== Est-ce qu'il a demandé un outil ? ===")
print(reponse.message.tool_calls)