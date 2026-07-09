import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { chatApi } from '../../services/api.js';

export const sendChatMessage = createAsyncThunk(
  'chat/send',
  async ({ message, currentInteractionId }, { getState, rejectWithValue }) => {
    try {
      const history = getState().chat.messages.map((m) => ({ role: m.role, content: m.content }));
      const response = await chatApi.send(message, currentInteractionId, history);
      return response;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || err.message);
    }
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [], // { role: 'user' | 'assistant', content, toolUsed }
    searchResults: [],
    historyResults: [],
    recommendation: null,
    status: 'idle',
    error: null,
  },
  reducers: {
    userMessageAdded(state, action) {
      state.messages.push({ role: 'user', content: action.payload });
    },
    chatReset(state) {
      state.messages = [];
      state.searchResults = [];
      state.historyResults = [];
      state.recommendation = null;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.status = 'succeeded';
        const data = action.payload;
        state.messages.push({ role: 'assistant', content: data.reply, toolUsed: data.tool_used });
        if (data.interactions) state.searchResults = data.interactions;
        if (data.tool_used === 'view_history' && data.interactions) {
          state.historyResults = data.interactions;
        }
        if (data.recommendation) state.recommendation = data.recommendation;
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
        state.messages.push({
          role: 'assistant',
          content: `Sorry, something went wrong: ${action.payload}`,
        });
      });
  },
});

export const { userMessageAdded, chatReset } = chatSlice.actions;
export default chatSlice.reducer;
