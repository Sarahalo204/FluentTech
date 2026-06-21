import { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../api/apiService';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // { learner_id, name, level }
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('edulingo_user');
    if (savedUser) {
      const parsed = JSON.parse(savedUser);
      setUser(parsed);
      if (parsed.access_token) {
        apiService.setToken(parsed.access_token);
      }
    }
    setIsLoading(false);
    setIsLoading(false);
  }, []);

  const login = async (email, password) => {
    const userData = await apiService.login({ email, password });
    setUser(userData);
    if (userData.access_token) apiService.setToken(userData.access_token);
    localStorage.setItem('edulingo_user', JSON.stringify(userData));
    return userData;
  };

  const register = async (data) => {
    // data contains {name, email, password, target_level, learning_goals, preferred_topics}
    const userData = await apiService.register(data);
    setUser(userData);
    if (userData.access_token) apiService.setToken(userData.access_token);
    localStorage.setItem('edulingo_user', JSON.stringify(userData));
    return userData;
  };

  const updateLevel = async (newLevel) => {
    if (!user) return;
    await apiService.updateLevel(user.learner_id, newLevel);
    const updatedUser = { ...user, level: newLevel };
    setUser(updatedUser);
    localStorage.setItem('edulingo_user', JSON.stringify(updatedUser));
  };

  const logout = () => {
    setUser(null);
    apiService.setToken(null);
    localStorage.removeItem('edulingo_user');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, updateLevel, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
