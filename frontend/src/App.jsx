import React, { useEffect, useRef, useState } from 'react';
import './App.css';

const API_URL = 'http://127.0.0.1:8000/chat';

const QUICK_REPLIES = [
  {
    label: '✦ Nouveautés',
    message: 'Voir vos nouveautés'
  },
  {
    label: '◷ Suivre ma commande',
    message: 'Suivre ma commande'
  },
  {
    label: '↩ Politique de retour',
    message: 'Politique de retour'
  }
];

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'agent',
      text:
        "Bienvenue chez Atlas Wear. Je suis votre conseiller personnel. Que souhaitez-vous découvrir ?"
    }
  ]);

  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  /* =====================================================
     AUTO SCROLL
  ===================================================== */

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth'
    });
  }, [messages, isLoading]);

  /* =====================================================
     SEND MESSAGE
  ===================================================== */

  const sendMessage = async (messageText) => {
    const text = messageText.trim();

    if (!text || isLoading) {
      return;
    }

    // Ajouter le message du client immédiatement
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        sender: 'client',
        text
      }
    ]);

    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json'
        },

        body: JSON.stringify({
          message: text
        })
      });

      if (!response.ok) {
        throw new Error(
          `Erreur API : ${response.status}`
        );
      }

      const data = await response.json();

      /*
       * IMPORTANT :
       * Ton backend FastAPI retourne :
       *
       * {
       *   "reponse": "..."
       * }
       */

      const agentText =
        data.reponse ??
        "Je suis désolé, je n'ai pas pu traiter votre demande.";

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'agent',
          text: agentText
        }
      ]);

    } catch (error) {
      console.error(
        'Erreur lors de la communication avec Atlas Wear:',
        error
      );

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'agent',
          text:
            "Je rencontre actuellement un problème de connexion. Veuillez réessayer dans quelques instants."
        }
      ]);

    } finally {
      setIsLoading(false);

      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    }
  };

  /* =====================================================
     FORM SUBMIT
  ===================================================== */

  const handleSend = async (event) => {
    event.preventDefault();

    await sendMessage(inputValue);
  };

  /* =====================================================
     QUICK REPLY
  ===================================================== */

  const handleQuickReply = async (message) => {
    await sendMessage(message);
  };

  return (
    <div className="page">

      <section className="chat-card">

        {/* =================================================
            HEADER
        ================================================= */}

        <header className="chat-header">

          <div className="chat-header-top">

            <div
              className="brand-mark"
              aria-label="Atlas Wear"
            >
              AW
            </div>

            <div className="brand-text">

              <h1>
                Atlas Wear
              </h1>

              <p>
                <span
                  className="status-dot"
                  aria-hidden="true"
                />

                Assistant IA&nbsp; • &nbsp;En ligne
              </p>

            </div>

          </div>

        </header>

        {/* =================================================
            GOLD SEPARATOR
        ================================================= */}

        <div
          className="zellige-band"
          aria-hidden="true"
        />

        {/* =================================================
            MESSAGES
        ================================================= */}

        <main
          className="messages"
          aria-live="polite"
          aria-label="Conversation avec Atlas Wear"
        >

          {messages.map((message) => (

            <div
              key={message.id}
              className={`message-row ${
                message.sender === 'client'
                  ? 'client'
                  : ''
              }`}
            >

              {message.sender === 'agent' && (
                <div
                  className="avatar"
                  aria-hidden="true"
                >
                  AW
                </div>
              )}

              <div
                className={`bubble ${message.sender}`}
              >
                {message.text}
              </div>

            </div>

          ))}

          {/* =================================================
              TYPING INDICATOR
          ================================================= */}

          {isLoading && (
            <div className="message-row">

              <div
                className="avatar"
                aria-hidden="true"
              >
                AW
              </div>

              <div
                className="bubble agent typing"
                aria-label="Atlas Wear est en train d'écrire"
              >

                <span className="dot" />
                <span className="dot" />
                <span className="dot" />

              </div>

            </div>
          )}

          {/* =================================================
              QUICK REPLIES
          ================================================= */}

          {!isLoading && messages.length === 1 && (
            <div
              className="quick-replies"
              aria-label="Suggestions"
            >

              {QUICK_REPLIES.map((item) => (

                <button
                  key={item.message}
                  type="button"
                  className="quick-reply"
                  onClick={() =>
                    handleQuickReply(item.message)
                  }
                >
                  {item.label}
                </button>

              ))}

            </div>
          )}

          <div ref={messagesEndRef} />

        </main>

        {/* =================================================
            INPUT
        ================================================= */}

        <form
          className="input-zone"
          onSubmit={handleSend}
        >

          <div className="input-zone-row">

            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              placeholder="Écrivez votre question..."
              aria-label="Votre question"
              autoComplete="off"
              disabled={isLoading}
              onChange={(event) =>
                setInputValue(event.target.value)
              }
            />

            <button
              type="submit"
              className="send-btn"
              aria-label="Envoyer le message"
              disabled={
                isLoading ||
                !inputValue.trim()
              }
            >

              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.4"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >

                <line
                  x1="22"
                  y1="2"
                  x2="11"
                  y2="13"
                />

                <polygon
                  points="22 2 15 22 11 13 2 9 22 2"
                />

              </svg>

            </button>

          </div>

          <div className="tagline">
            Assistant IA disponible à tout moment
          </div>

        </form>

      </section>

    </div>
  );
}