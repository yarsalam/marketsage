'use client';

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import axiosWithAuth from '@/lib/axiosWithAuth';

export interface AppUser {
  id: number;
  nickname: string;
  role: 'owner';
}

interface AuthContextType {
  user: AppUser | null;
  isAuthenticated: boolean;
  isAuthLoading: boolean;
  refreshSession: () => Promise<boolean>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AppUser | null>(null);
  const [isAuthLoading, setAuthLoading] = useState(true);

  const refreshSession = useCallback(async (): Promise<boolean> => {
    setAuthLoading(true);
    try {
      const response = await axiosWithAuth.get<AppUser>('/auth/me');
      setUser(response.data);
      return true;
    } catch {
      setUser(null);
      return false;
    } finally {
      setAuthLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshSession();
  }, [refreshSession]);

  const logout = useCallback(async () => {
    try {
      await axiosWithAuth.post('/auth/logout');
    } finally {
      setUser(null);
      queryClient.clear();
    }
  }, [queryClient]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isAuthLoading,
        refreshSession,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
