import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { message } from 'antd';
import authService from '../services/authService';

export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  role: 'admin' | 'manager' | 'user';
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  register: (data: RegisterData) => Promise<void>;
  isAdmin: () => boolean;
  isManager: () => boolean;
  hasPermission: (requiredRole: 'admin' | 'manager' | 'user') => boolean;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load token and user from localStorage on mount
    const storedToken = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('auth_user');

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      authService.setAuthToken(storedToken);
      
      // Validate token by fetching current user
      authService.getCurrentUser()
        .then(userData => {
          setUser(userData);
          localStorage.setItem('auth_user', JSON.stringify(userData));
        })
        .catch(() => {
          // Token is invalid, clear auth
          logout();
        });
    }
    
    setLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await authService.login(username, password);
      const { access_token, user: userData } = response;
      
      setToken(access_token);
      setUser(userData);
      
      localStorage.setItem('auth_token', access_token);
      localStorage.setItem('auth_user', JSON.stringify(userData));
      
      authService.setAuthToken(access_token);
      
      message.success('로그인 성공!');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '로그인에 실패했습니다.');
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    authService.clearAuthToken();
    message.info('로그아웃되었습니다.');
  };

  const register = async (data: RegisterData) => {
    try {
      const response = await authService.register(data);
      message.success('회원가입이 완료되었습니다. 로그인해주세요.');
      return response;
    } catch (error: any) {
      message.error(error.response?.data?.detail || '회원가입에 실패했습니다.');
      throw error;
    }
  };

  const isAdmin = () => {
    return user?.role === 'admin';
  };

  const isManager = () => {
    return user?.role === 'manager' || user?.role === 'admin';
  };

  const hasPermission = (requiredRole: 'admin' | 'manager' | 'user') => {
    if (!user) return false;
    
    const roleHierarchy = {
      admin: 3,
      manager: 2,
      user: 1,
    };
    
    return roleHierarchy[user.role] >= roleHierarchy[requiredRole];
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    register,
    isAdmin,
    isManager,
    hasPermission,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;