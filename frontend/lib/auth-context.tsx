'use client';

/**
 * Authentication context provider for global auth state management.
 *
 * Provides user authentication state, login/logout functions, and automatic
 * token refresh functionality across the application.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import type { User, LoginCredentials, RegisterCredentials } from './auth-types';
import { AuthAPI } from './auth-api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  /**
   * Get access token from cookies.
   */
  const getAccessToken = useCallback((): string | undefined => {
    return Cookies.get(ACCESS_TOKEN_KEY);
  }, []);

  /**
   * Get refresh token from cookies.
   */
  const getRefreshToken = useCallback((): string | undefined => {
    return Cookies.get(REFRESH_TOKEN_KEY);
  }, []);

  /**
   * Store tokens in cookies.
   */
  const storeTokens = useCallback((accessToken: string, refreshToken: string) => {
    // Access token expires in 15 minutes
    Cookies.set(ACCESS_TOKEN_KEY, accessToken, {
      expires: 1/96,  // 15 minutes
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax'
    });

    // Refresh token expires in 7 days
    Cookies.set(REFRESH_TOKEN_KEY, refreshToken, {
      expires: 7,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax'
    });
  }, []);

  /**
   * Clear tokens from cookies.
   */
  const clearTokens = useCallback(() => {
    Cookies.remove(ACCESS_TOKEN_KEY);
    Cookies.remove(REFRESH_TOKEN_KEY);
  }, []);

  /**
   * Fetch user profile from API.
   */
  const fetchUser = useCallback(async () => {
    const accessToken = getAccessToken();

    if (!accessToken) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const userData = await AuthAPI.getProfile(accessToken);
      setUser(userData);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch user:', err);

      const status = err?.response?.status;

      // Only clear tokens on auth errors (401/403), not server errors (500)
      if (status && status >= 500) {
        console.warn('Server error fetching profile, keeping tokens');
        setLoading(false);
        return;
      }

      // Try to refresh token if access token expired
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        try {
          const tokens = await AuthAPI.refreshToken(refreshToken);
          storeTokens(tokens.access_token, tokens.refresh_token);

          // Retry fetching user with new token
          const userData = await AuthAPI.getProfile(tokens.access_token);
          setUser(userData);
          setError(null);
        } catch (refreshErr: any) {
          console.error('Token refresh failed:', refreshErr);
          const refreshStatus = refreshErr?.response?.status;
          // Only clear tokens on auth errors, not server errors
          if (!refreshStatus || refreshStatus < 500) {
            clearTokens();
            setUser(null);
          }
        }
      } else {
        clearTokens();
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, getRefreshToken, storeTokens, clearTokens]);

  /**
   * Login with email and password.
   */
  const login = useCallback(async (credentials: LoginCredentials) => {
    setLoading(true);
    setError(null);

    try {
      const tokens = await AuthAPI.login(credentials);
      storeTokens(tokens.access_token, tokens.refresh_token);

      // Fetch user profile
      const userData = await AuthAPI.getProfile(tokens.access_token);
      setUser(userData);

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Login failed. Please check your credentials.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [storeTokens, router]);

  /**
   * Register new user account.
   */
  const register = useCallback(async (credentials: RegisterCredentials) => {
    setLoading(true);
    setError(null);

    try {
      // Register user
      await AuthAPI.register(credentials);

      // Automatically login after registration
      await login({
        email: credentials.email,
        password: credentials.password,
      });
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Registration failed. Please try again.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [login]);

  /**
   * Logout and clear session.
   */
  const logout = useCallback(() => {
    const accessToken = getAccessToken();

    // Call logout API (optional - tokens are stateless)
    if (accessToken) {
      AuthAPI.logout(accessToken).catch(console.error);
    }

    // Clear local state
    clearTokens();
    setUser(null);
    setError(null);

    // Redirect to login page
    router.push('/auth/login');
  }, [getAccessToken, clearTokens, router]);

  /**
   * Refresh user profile data.
   */
  const refreshUser = useCallback(async () => {
    await fetchUser();
  }, [fetchUser]);

  // Fetch user on mount
  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  // Auto-refresh token before expiry (every 10 minutes)
  useEffect(() => {
    const interval = setInterval(async () => {
      const refreshToken = getRefreshToken();

      if (refreshToken && user) {
        try {
          const tokens = await AuthAPI.refreshToken(refreshToken);
          storeTokens(tokens.access_token, tokens.refresh_token);
        } catch (err) {
          console.error('Auto token refresh failed:', err);
          logout();
        }
      }
    }, 10 * 60 * 1000); // 10 minutes

    return () => clearInterval(interval);
  }, [user, getRefreshToken, storeTokens, logout]);

  const value: AuthContextType = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access authentication context.
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}

/**
 * Hook to get access token for API calls.
 */
export function useAccessToken(): string | undefined {
  return Cookies.get(ACCESS_TOKEN_KEY);
}
