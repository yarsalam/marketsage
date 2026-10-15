// src/context/AuthContext.tsx
'use client';
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { decodeToken } from '@/lib/decodeToken';
import axiosWithAuth from '@/lib/axiosWithAuth';

export interface AppUser {
  id: number;
  nickname: string;
  email?: string;
  tier?: string;
}

interface AuthContextType {
  user: AppUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isAuthLoading: boolean;
  setToken: (token: string | null) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const queryClient = useQueryClient();
  const [token, setTokenState] = useState<string | null>(null);
  const [isAuthLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('auth_token');
    setTokenState(stored);
    setAuthLoading(false);
  }, []);

  const decoded = token ? decodeToken(token) : null;
  const isPermanent = !!token && decoded?.temporary !== true;

  const { data: user, error } = useQuery<AppUser>({
    queryKey: ['me'],
    queryFn: () => axiosWithAuth.get('/auth/me').then((res) => res.data),
    enabled: isPermanent,
    retry: false,
  });

  useEffect(() => {
    if (isPermanent && error) {
      localStorage.removeItem('auth_token');
      setTokenState(null);
      queryClient.removeQueries({ queryKey: ['me'] });
    }
  }, [error, isPermanent, queryClient]);

  const isAuthenticated = Boolean(isPermanent && user);

  const setToken = useCallback(
    async (newToken: string | null) => {
      if (newToken) {
        localStorage.setItem('auth_token', newToken);
        setTokenState(newToken);
        const d = decodeToken(newToken);
        if (d?.temporary !== true) {
          try {
            await queryClient.fetchQuery({
              queryKey: ['me'],
              queryFn: () =>
                axiosWithAuth.get('/auth/me').then((res) => res.data),
            });
          } catch {
            localStorage.removeItem('auth_token');
            setTokenState(null);
          }
        }
      } else {
        localStorage.removeItem('auth_token');
        setTokenState(null);
        queryClient.removeQueries({ queryKey: ['me'] });
      }
    },
    [queryClient],
  );

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    setTokenState(null);
    queryClient.removeQueries({ queryKey: ['me'] });
    queryClient.clear();
  }, [queryClient]);

  return (
    <AuthContext.Provider
      value={{
        user: user || null,
        token,
        isAuthenticated,
        isAuthLoading,
        setToken,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
