import React, { createContext, useState, useEffect, useContext } from 'react';

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  tenant_id: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (token: string, userData: User) => void;
  logout: () => void;
  apiFetch: (path: string, options?: RequestInit) => Promise<any>;
  apiUrl: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const API_BASE = "http://localhost:8000/api";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const savedToken = localStorage.getItem('sentinel_token');
    const savedUser = localStorage.getItem('sentinel_user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = (newToken: string, userData: User) => {
    localStorage.setItem('sentinel_token', newToken);
    localStorage.setItem('sentinel_user', JSON.stringify(userData));
    setToken(newToken);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('sentinel_token');
    localStorage.removeItem('sentinel_user');
    setToken(null);
    setUser(null);
  };

  const apiFetch = async (path: string, options: RequestInit = {}) => {
    const headers = new Headers(options.headers || {});
    
    // Add auth token if available
    const activeToken = token || localStorage.getItem('sentinel_token');
    if (activeToken) {
      headers.set("Authorization", `Bearer ${activeToken}`);
    }

    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers
    });

    if (res.status === 401) {
      logout();
      throw new Error("Session expired. Please log in again.");
    }

    if (res.status === 204) {
      return null;
    }

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Request failed.");
    }

    return data;
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, apiFetch, apiUrl: API_BASE }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
