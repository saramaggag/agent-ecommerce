# Atlas Wear — Agent IA de Support Client

Agent conversationnel intelligent pour une boutique e-commerce marocaine (fictive), combinant **RAG**, **tool calling** et **escalade automatique** pour répondre aux questions clients en temps réel — catalogue produits, stock exact, suivi de commande, politiques de retour.

**🔗 Démo en ligne :** [agent-ecommerce-one.vercel.app](https://agent-ecommerce-one.vercel.app)

> ⏳ Le backend est hébergé sur un plan gratuit (Railway) : après une période d'inactivité, la première réponse peut prendre 10 à 30 secondes le temps que le service se réveille. C'est normal.

---

## 📸 Aperçu

Interface de chat avec identité visuelle propre à Atlas Wear (palette noir/or, typographie Fraunces + Manrope, bande décorative géométrique inspirée du zellige marocain).

---

## ✨ Fonctionnalités

- **RAG (Retrieval-Augmented Generation)** — répond aux questions sur le catalogue produits et la FAQ (livraison, paiement, retours) à partir d'une base vectorielle
- **Tool calling** — vérifie une donnée exacte et à jour via de vraies requêtes SQL :
  - `consulter_stock` — quantité disponible par produit, taille et couleur
  - `suivre_commande` — statut, montant et date d'une commande
- **Escalade automatique** — transfère vers un humain toute question hors périmètre, avec un filet de sécurité côté code (pas seulement une consigne au LLM)
- **Garde-fous anti-hallucination** — system prompt strict, température à 0, et vérification systématique côté code plutôt que confiance aveugle envers le modèle
- **Double environnement LLM** — Ollama en local pour le développement (gratuit, sans API externe), bascule automatique vers Groq en production (l'hébergement gratuit ne supporte pas de faire tourner un LLM local)

---

## 🏗️ Architecture

```
Client (navigateur)
      │
      ▼
Frontend React (Vercel)
      │  POST /chat
      ▼
Backend FastAPI (Railway, conteneur Docker)
      │
      ├──▶ ChromaDB (RAG — catalogue + FAQ)
      │
      ├──▶ PostgreSQL / Neon (stock, commandes, clients)
      │
      └──▶ LLM : Ollama (dev local) ou Groq (production)
```

**Logique de décision de l'agent :**
1. Recherche RAG systématique, avant tout appel au LLM
2. Le LLM reçoit la question, le contexte RAG trouvé (si pertinent) et la liste des outils disponibles
3. Il décide : répondre directement (info stable), appeler un outil (donnée exacte et variable), ou signaler qu'il ne sait pas
4. Si aucun outil n'est appelé et qu'aucun contexte RAG fiable n'existe, le **code** force l'escalade — jamais une réponse improvisée

---

## 🛠️ Stack technique — 100% gratuit

| Composant | Outil |
|---|---|
| LLM (développement) | Ollama + `qwen2.5:3b` |
| LLM (production) | Groq + `openai/gpt-oss-20b` |
| Modèle d'embedding (dev) | `nomic-embed-text` via Ollama |
| Modèle d'embedding (prod) | Modèle par défaut de ChromaDB (`all-MiniLM-L6-v2`) |
| Base vectorielle | ChromaDB |
| Base relationnelle | PostgreSQL (Neon en production) |
| Backend | FastAPI |
| Frontend | React (Vite) |
| Conteneurisation | Docker |
| Hébergement backend | Railway |
| Hébergement frontend | Vercel |
| Base de données hébergée | Neon |

---

## 📁 Structure du projet

```
agent-ecommerce/
├── backend/
│   ├── agent_stock.py          # Cœur de l'agent : RAG + outils + décision
│   ├── main.py                 # API FastAPI (endpoint POST /chat)
│   ├── ingest_chroma.py        # Ingestion ChromaDB (développement, Ollama)
│   ├── ingest_chroma_prod.py   # Ingestion ChromaDB (production, embedding par défaut)
│   ├── calibrer_rag.py         # Calibration du seuil RAG (développement)
│   ├── calibrer_rag_prod.py    # Calibration du seuil RAG (production)
│   ├── seed_postgres.py        # Peuplement produits + stock
│   ├── seed_commandes.py       # Peuplement clients + commandes
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── chroma_data_prod/       # Données RAG de production (commité, utilisé par Docker)
│   └── chroma_data/            # Données RAG locales (git-ignoré)
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── App.css
├── data/
│   ├── produits.json
│   └── faq.json
├── docker-compose.yml           # Environnement de développement local
└── README.md
```

---

## 🚀 Lancer le projet en local

### Prérequis
- Python 3.11+, Node.js, Docker Desktop
- [Ollama](https://ollama.com) installé, avec les modèles `qwen2.5:3b` et `nomic-embed-text` téléchargés
- PostgreSQL (ou utiliser directement `docker-compose`)

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Crée un fichier `.env` dans `backend/` :
```
DB_PASSWORD=ton_mot_de_passe_postgresql
```

Ingestion des données (une seule fois) :
```bash
python ingest_chroma.py
python seed_postgres.py
python seed_commandes.py
```

Lancement :
```bash
python -m uvicorn main:app --reload
```

### Avec Docker (backend + PostgreSQL ensemble)

```bash
docker-compose up --build
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Interface disponible sur `http://localhost:5173`.

---

## ⚠️ Limites connues

Ce projet est un portfolio d'apprentissage — ces limites sont documentées volontairement plutôt que cachées :

- **Une seule couleur de stock par produit** — le peuplement initial n'a enregistré qu'une couleur "principale" par article ; une recherche par couleur retourne le stock toutes tailles confondues pour cette couleur, pas une vraie combinaison couleur × taille
- **Une intention par message** — une question combinant deux demandes différentes (ex. *"vous avez des jeans et vous livrez où ?"*) peut ne recevoir de réponse que sur une seule partie ; limite du modèle de génération, pas du code
- **Darija en écriture latine** — bien géré pour les questions de stock simples, moins fiable sur des questions FAQ complexes
- **Ambiguïté "produit inexistant" vs "rupture de stock"** — l'outil de consultation de stock retourne `0` dans les deux cas, sans les distinguer explicitement

---

## 📄 Cahier des charges

Le cahier des charges complet du projet (contexte, spécifications, planning) est disponible dans `Cahier_des_charges_Agent_IA_Ecommerce.docx`.

---

## 👤 Auteure

**Sara Maggag** — Data Scientist
[GitHub](https://github.com/saramaggag) · [LinkedIn](#)

Projet réalisé dans un objectif d'apprentissage intégré : combiner RAG, agent IA, backend, frontend, Docker et déploiement dans un seul projet réaliste plutôt que théoriquement séparé.
