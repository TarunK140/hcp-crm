import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { interactionApi } from '../../services/api.js';

const emptyInteraction = {
  id: null,
  hcp_name: '',
  interaction_type: 'In-Person',
  date: new Date().toISOString().slice(0, 10),
  time: '',
  attendees: '',
  topics_discussed: '',
  materials_shared: '',
  samples_distributed: '',
  sentiment: 'Neutral',
  outcomes: '',
  follow_up: '',
};

export const saveInteraction = createAsyncThunk(
  'interaction/save',
  async (formData, { rejectWithValue }) => {
    try {
      const payload = { ...formData };
      delete payload.id;
      delete payload.created_at;
      delete payload.updated_at;
      if (!payload.time) delete payload.time;

      if (formData.id) {
        return await interactionApi.update(formData.id, payload);
      }
      return await interactionApi.create(payload);
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || err.message);
    }
  }
);

export const loadInteraction = createAsyncThunk(
  'interaction/load',
  async (id, { rejectWithValue }) => {
    try {
      return await interactionApi.get(id);
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || err.message);
    }
  }
);

const interactionSlice = createSlice({
  name: 'interaction',
  initialState: {
    current: emptyInteraction,
    status: 'idle', // idle | loading | succeeded | failed
    error: null,
    lastSavedAt: null,
  },
  reducers: {
    fieldChanged(state, action) {
      const { field, value } = action.payload;
      state.current[field] = value;
    },
    interactionReplaced(state, action) {
      // Called when the AI assistant returns an updated interaction —
      // this is the "FastAPI -> Redux -> React Form" sync path.
      state.current = { ...state.current, ...action.payload };
    },
    formReset(state) {
      state.current = emptyInteraction;
      state.error = null;
      state.status = 'idle';
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(saveInteraction.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(saveInteraction.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.current = action.payload;
        state.lastSavedAt = new Date().toISOString();
      })
      .addCase(saveInteraction.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })
      .addCase(loadInteraction.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(loadInteraction.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.current = action.payload;
      })
      .addCase(loadInteraction.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      });
  },
});

export const { fieldChanged, interactionReplaced, formReset } = interactionSlice.actions;
export default interactionSlice.reducer;
