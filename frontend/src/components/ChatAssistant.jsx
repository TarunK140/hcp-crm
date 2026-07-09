import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { sendChatMessage, userMessageAdded } from '../redux/slices/chatSlice.js';
import { interactionReplaced } from '../redux/slices/interactionSlice.js';

function renderBold(text) {
  // Lightweight **bold** -> <strong> renderer for the AI's confirmation messages.
  const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const html = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  return { __html: html };
}

const SUCCESS_TOOLS = new Set([
  'log_interaction',
  'edit_interaction',
  'search_interaction',
  'view_history',
  'follow_up_recommendation',
]);

export default function ChatAssistant() {
  const dispatch = useDispatch();
  const { messages, searchResults, historyResults, recommendation, status } = useSelector(
    (s) => s.chat
  );
  const currentInteractionId = useSelector((s) => s.interaction.current.id);
  const [input, setInput] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, searchResults, historyResults, recommendation]);

  const handleSend = async (e) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

    dispatch(userMessageAdded(trimmed));
    setInput('');

    const action = await dispatch(sendChatMessage({ message: trimmed, currentInteractionId }));

    // Sync path: LangGraph result -> Redux -> Form (auto-fills/updates the left pane).
    if (sendChatMessage.fulfilled.match(action) && action.payload.interaction) {
      dispatch(interactionReplaced(action.payload.interaction));
    }
  };

  const bubbleClass = (m) => {
    if (m.role === 'user') return 'chat-bubble user';
    if (m.toolUsed && SUCCESS_TOOLS.has(m.toolUsed) && !/error|sorry/i.test(m.content)) {
      return 'chat-bubble assistant success';
    }
    if (/sorry|error|failed/i.test(m.content)) return 'chat-bubble assistant error';
    return 'chat-bubble assistant';
  };

  return (
    <>
      <div className="chat-header">
        <div className="chat-avatar">🤖</div>
        <div>
          <div className="chat-header-title">AI Assistant</div>
          <div className="chat-header-subtitle">Log interaction details here via chat</div>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-bubble system">
            Log interaction details here (e.g., "Met Dr. Smith, discussed Prodo-X efficacy,
            positive sentiment, shared brochure") or ask for help.
          </div>
        )}

        {messages.map((m, idx) => (
          <div key={idx} className={`chat-row ${m.role}`}>
            <div className={`chat-mini-avatar ${m.role}`}>{m.role === 'user' ? '🧑' : '🤖'}</div>
            <div className={bubbleClass(m)}>
              {m.role === 'assistant' && m.toolUsed && (
                <div className="tool-tag">{m.toolUsed.replaceAll('_', ' ')}</div>
              )}
              {m.role === 'assistant' ? (
                <span
                  dangerouslySetInnerHTML={renderBold(
                    `${bubbleClass(m).includes('success') ? '✅ ' : ''}${m.content}`
                  )}
                />
              ) : (
                m.content
              )}
            </div>
          </div>
        ))}

        {status === 'loading' && (
          <div className="chat-row assistant">
            <div className="chat-mini-avatar assistant">🤖</div>
            <div className="chat-bubble assistant">Thinking...</div>
          </div>
        )}

        {searchResults?.length > 0 && (
          <div className="results-list">
            {searchResults.map((r) => (
              <div key={r.id} className="result-card">
                <strong>#{r.id} — {r.hcp_name}</strong>
                <div>{r.interaction_type} · {r.date} · {r.sentiment}</div>
              </div>
            ))}
          </div>
        )}

        {recommendation && (
          <div className="result-card">
            <strong>Follow-up Recommendation — {recommendation.hcp_name}</strong>
            <div>Next visit: {recommendation.next_visit_timing}</div>
            <div>Materials: {recommendation.suggested_materials}</div>
            <div>Samples: {recommendation.suggested_samples}</div>
            <div>Talking points: {recommendation.conversation_points}</div>
            <div>Actions: {recommendation.follow_up_actions}</div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form className="chat-input-row" onSubmit={handleSend}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe interaction..."
        />
        <button type="submit" className="btn-log" disabled={status === 'loading'}>
          ➤ Log
        </button>
      </form>
    </>
  );
}

