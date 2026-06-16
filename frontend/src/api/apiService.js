import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  setToken(token) {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  },
  // --- Auth & Profile ---
  async register(data) {
    const response = await api.post('/auth/register', data);
    return response.data;
  },
  
  async login(learnerId) {
    const response = await api.post('/auth/login', { learner_id: learnerId });
    return response.data;
  },

  async updateLevel(learnerId, newLevel) {
    const response = await api.post('/auth/update_level', { learner_id: learnerId, new_level: newLevel });
    return response.data;
  },

  // --- Progress & Analytics ---
  async getProgress(learnerId) {
    const response = await api.get(`/api/progress/${learnerId}`);
    return response.data;
  },

  // --- Chat & Agents ---
  async sendMessage(learnerId, sessionId, message, sessionType = "conversation") {
    const response = await api.post('/api/chat', {
      learner_id: learnerId,
      session_id: sessionId,
      user_input: message,
      session_type: sessionType
    });
    return {
      response: response.data.response,
      agentUsed: response.data.agent_used,
      feedback: response.data.feedback
    };
  },

  // --- Exercises ---
  async generateExercise(learnerId, exerciseType, topicOrWeakness) {
    const response = await api.post('/api/exercises', {
      learner_id: learnerId,
      exercise_type: exerciseType,
      topic_or_weakness: topicOrWeakness
    });
    return response.data;
  }
};
