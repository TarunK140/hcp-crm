import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fieldChanged, saveInteraction, formReset } from '../redux/slices/interactionSlice.js';

const INTERACTION_TYPES = ['In-Person', 'Virtual', 'Phone', 'Email'];
const SENTIMENTS = [
  { value: 'Positive', emoji: '😊' },
  { value: 'Neutral', emoji: '😐' },
  { value: 'Negative', emoji: '😟' },
];

export default function InteractionForm() {
  const dispatch = useDispatch();
  const { current, status, error, lastSavedAt } = useSelector((s) => s.interaction);

  const handleChange = (field) => (e) => {
    dispatch(fieldChanged({ field, value: e.target.value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(saveInteraction(current));
  };

  const handleNew = () => {
    dispatch(formReset());
  };

  const handleVoiceNote = () => {
    alert(
      'Voice note summarization requires microphone consent and is not wired up in this build — the AI chat assistant on the right is the primary way to auto-fill this form from natural language.'
    );
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="card">
        <div className="form-section-title">📋 Log HCP Interaction</div>
        <div className="form-section-subtitle">
          Fill manually below, or describe it to the AI assistant on the right.
        </div>

        {status === 'succeeded' && lastSavedAt && (
          <div className="status-banner success">
            ✅ Saved successfully {current.id ? `(Interaction #${current.id})` : ''}
          </div>
        )}
        {status === 'failed' && error && (
          <div className="status-banner error">⚠️ Error: {String(error)}</div>
        )}
      </div>

      <div className="card">
        <div className="form-subsection-title">Interaction Details</div>
        <div className="form-grid">
          <div className="form-field">
            <label>HCP Name</label>
            <input
              type="text"
              value={current.hcp_name}
              onChange={handleChange('hcp_name')}
              placeholder="Search or select HCP..."
              required
            />
          </div>

          <div className="form-field">
            <label>Interaction Type</label>
            <select value={current.interaction_type} onChange={handleChange('interaction_type')} required>
              {INTERACTION_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="form-field">
            <label>Date</label>
            <input type="date" value={current.date} onChange={handleChange('date')} required />
          </div>

          <div className="form-field">
            <label>Time</label>
            <input type="time" value={current.time || ''} onChange={handleChange('time')} />
          </div>

          <div className="form-field full-width">
            <label>Attendees</label>
            <input
              type="text"
              value={current.attendees || ''}
              onChange={handleChange('attendees')}
              placeholder="Enter names or search..."
            />
          </div>

          <div className="form-field full-width">
            <label>Topics Discussed</label>
            <textarea
              value={current.topics_discussed || ''}
              onChange={handleChange('topics_discussed')}
              placeholder="Enter key discussion points..."
            />
            <button type="button" className="voice-note-link" onClick={handleVoiceNote}>
              🎙️ Summarize from Voice Note (Requires Consent)
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="form-subsection-title">Materials Shared / Samples Distributed</div>
        <div className="form-field full-width">
          <label>Materials Shared</label>
          <div className="field-with-action">
            <input
              type="text"
              value={current.materials_shared || ''}
              onChange={handleChange('materials_shared')}
              placeholder="No materials added."
            />
            <button type="button" className="btn-inline">
              🔍 Search/Add
            </button>
          </div>
        </div>

        <div className="form-field full-width">
          <label>Samples Distributed</label>
          <div className="field-with-action">
            <input
              type="text"
              value={current.samples_distributed || ''}
              onChange={handleChange('samples_distributed')}
              placeholder="No samples added."
            />
            <button type="button" className="btn-inline">
              + Add Sample
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="form-subsection-title">Observed/Inferred HCP Sentiment</div>
        <div className="sentiment-options">
          {SENTIMENTS.map(({ value, emoji }) => (
            <label key={value} className="sentiment-option">
              <input
                type="radio"
                name="sentiment"
                value={value}
                checked={(current.sentiment || 'Neutral') === value}
                onChange={handleChange('sentiment')}
              />
              {emoji} {value}
            </label>
          ))}
        </div>

        <div className="form-field full-width" style={{ marginTop: 16 }}>
          <label>Outcomes</label>
          <textarea
            value={current.outcomes || ''}
            onChange={handleChange('outcomes')}
            placeholder="Key outcomes or agreements..."
          />
        </div>

        <div className="form-field full-width">
          <label>Follow-up Actions</label>
          <textarea value={current.follow_up || ''} onChange={handleChange('follow_up')} />
        </div>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={status === 'loading'}>
          {status === 'loading' ? 'Saving...' : current.id ? '✓ Update Interaction' : '✓ Submit'}
        </button>
        <button type="button" className="btn-secondary" onClick={handleNew}>
          + New Interaction
        </button>
      </div>
    </form>
  );
}

