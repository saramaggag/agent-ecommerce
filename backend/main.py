from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent_stock import repondre

app = FastAPI(title="Atlas Wear - Agent IA")

# Autorise les requêtes venant du frontend React (autre port, sinon le navigateur bloque)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à restreindre plus tard en production
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    message: str

@app.get("/")
def accueil():
    return {"status": "Atlas Wear agent en ligne"}

@app.post("/chat")
def chat(question: Question):
    reponse = repondre(question.message)
    return {"reponse": reponse}