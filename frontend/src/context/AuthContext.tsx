'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import axios from 'axios';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, role: string, userId: string, fullName: string) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Load auth from localStorage on boot
    const storedToken = localStorage.getItem('olt_noc_token');
    const storedRole = localStorage.getItem('olt_noc_role');
    const storedUserId = localStorage.getItem('olt_noc_userid');
    const storedName = localStorage.getItem('olt_noc_fullname');
    const storedEmail = localStorage.getItem('olt_noc_email') || 'admin@oltnoc.local';

    if (storedToken && storedRole && storedUserId && storedName) {
      setToken(storedToken);
      setUser({
        id: storedUserId,
        email: storedEmail,
        full_name: storedName,
        role: storedRole
      });
      // Setup Axios default authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
    } else {
      // If no token, redirect to login unless on login page
      if (pathname !== '/' && pathname !== '/login') {
        router.push('/');
      }
    }
    setIsLoading(false);
  }, [pathname, router]);

  const login = (jwtToken: string, role: string, userId: string, fullName: string) => {
    localStorage.setItem('olt_noc_token', jwtToken);
    localStorage.setItem('olt_noc_role', role);
    localStorage.setItem('olt_noc_userid', userId);
    localStorage.setItem('olt_noc_fullname', fullName);
    localStorage.setItem('olt_noc_email', 'admin@oltnoc.local');
    
    setToken(jwtToken);
    setUser({
      id: userId,
      email: 'admin@oltnoc.local',
      full_name: fullName,
      role: role
    });
    
    axios.defaults.headers.common['Authorization'] = `Bearer ${jwtToken}`;
    router.push('/dashboard');
  };

  const logout = () => {
    localStorage.clear();
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
    router.push('/');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
