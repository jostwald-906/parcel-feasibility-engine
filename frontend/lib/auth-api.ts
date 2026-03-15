/**
 * Authentication API client for user login, registration, and token management.
 */
import axios from 'axios';
import type {
  User,
  LoginCredentials,
  RegisterCredentials,
  AuthTokens,
  Subscription,
  UsageStats,
  CheckoutSession,
  PortalSession,
} from './auth-types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class AuthAPI {
  /**
   * Register a new user account.
   */
  static async register(credentials: RegisterCredentials): Promise<User> {
    const response = await axios.post<User>(
      `${API_URL}/api/v1/auth/register`,
      credentials
    );
    return response.data;
  }

  /**
   * Login with email and password.
   * Returns JWT tokens.
   */
  static async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await axios.post<AuthTokens>(
      `${API_URL}/api/v1/auth/login`,
      credentials
    );
    return response.data;
  }

  /**
   * Refresh access token using refresh token.
   */
  static async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await axios.post<AuthTokens>(
      `${API_URL}/api/v1/auth/refresh`,
      {},
      {
        headers: {
          Authorization: `Bearer ${refreshToken}`,
        },
      }
    );
    return response.data;
  }

  /**
   * Logout (client-side token deletion).
   */
  static async logout(accessToken: string): Promise<void> {
    await axios.post(
      `${API_URL}/api/v1/auth/logout`,
      {},
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );
  }

  /**
   * Get current user profile.
   */
  static async getProfile(accessToken: string): Promise<User> {
    const response = await axios.get<User>(`${API_URL}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
    return response.data;
  }

  /**
   * Update current user profile.
   */
  static async updateProfile(
    accessToken: string,
    updates: Partial<RegisterCredentials>
  ): Promise<User> {
    const response = await axios.patch<User>(
      `${API_URL}/api/v1/auth/me`,
      updates,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );
    return response.data;
  }
}

export class PaymentAPI {
  /**
   * Create a Stripe checkout session for Pro subscription.
   */
  static async createCheckoutSession(
    accessToken: string
  ): Promise<CheckoutSession> {
    const response = await axios.post<CheckoutSession>(
      `${API_URL}/api/v1/payments/create-checkout-session`,
      {},
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );
    return response.data;
  }

  /**
   * Create a Stripe Customer Portal session for managing billing.
   */
  static async createPortalSession(
    accessToken: string
  ): Promise<PortalSession> {
    const response = await axios.post<PortalSession>(
      `${API_URL}/api/v1/payments/create-portal-session`,
      {},
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );
    return response.data;
  }

  /**
   * Get current user's subscription details.
   */
  static async getSubscription(accessToken: string): Promise<Subscription> {
    const response = await axios.get<Subscription>(
      `${API_URL}/api/v1/payments/subscription`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );
    return response.data;
  }

  /**
   * Get current user's usage statistics.
   */
  static async getUsageStats(accessToken: string): Promise<UsageStats> {
    const response = await axios.get<UsageStats>(
      `${API_URL}/api/v1/payments/usage`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );
    return response.data;
  }
}
