import { configureStore } from '@reduxjs/toolkit';
import interactionReducer from './slices/interactionSlice.js';
import chatReducer from './slices/chatSlice.js';

export const store = configureStore({
  reducer: {
    interaction: interactionReducer,
    chat: chatReducer,
  },
});
