import { useState } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([
    { role: 'agent', text: 'Bonjour ! Je suis l\'assistant Atlas Wear. Comment puis-je vous aider ?' }
  ])
  const [input, setInput] = useState('')
  const [chargement, setChargement] = useState(false)

  const envoyerMessage = async () => {
    if (!input.trim()) return

    const messageClient = input
    setMessages(prev => [...prev, { role: 'client', text: messageClient }])
    setInput('')
    setChargement(true)

    try {
      const reponse = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageClient })
      })
      const data = await reponse.json()
      setMessages(prev => [...prev, { role: 'agent', text: data.reponse }])
    } catch (erreur) {
      setMessages(prev => [...prev, { role: 'agent', text: 'Erreur de connexion au serveur. Vérifiez que l\'API tourne bien.' }])
    } finally {
      setChargement(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') envoyerMessage()
  }

  return (
    <div className="chat-container">
      <h1>Atlas Wear — Support Client</h1>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.text}
          </div>
        ))}
        {chargement && <div className="message agent">En train d'écrire...</div>}
      </div>
      <div className="input-zone">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Écrivez votre question..."
        />
        <button onClick={envoyerMessage}>Envoyer</button>
      </div>
    </div>
  )
}

export default App