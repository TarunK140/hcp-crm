import React from 'react';
import InteractionForm from '../components/InteractionForm.jsx';
import ChatAssistant from '../components/ChatAssistant.jsx';

export default function LogInteractionPage() {
  return (
    <div className="split-screen">
      <div className="left-pane">
        <InteractionForm />
      </div>
      <div className="right-pane">
        <ChatAssistant />
      </div>
    </div>
  );
}
