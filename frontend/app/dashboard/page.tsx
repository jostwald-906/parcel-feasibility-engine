'use client';

import { useState, useEffect } from 'react';
import { useAuth, useAccessToken } from '@/lib/auth-context';
import { PaymentAPI } from '@/lib/auth-api';
import {
  Building2,
  User,
  CreditCard,
  BarChart3,
  LogOut,
  Settings,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
} from 'lucide-react';
import Link from 'next/link';
import type { Subscription, UsageStats } from '@/lib/auth-types';
import { SubscriptionStatus } from '@/lib/auth-types';

export default function DashboardPage() {
  const { user, logout, loading: authLoading } = useAuth();
  const accessToken = useAccessToken();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => {
    if (!accessToken) return;

    const fetchData = async () => {
      try {
        const [subData, usageData] = await Promise.all([
          PaymentAPI.getSubscription(accessToken).catch(() => null),
          PaymentAPI.getUsageStats(accessToken).catch(() => null),
        ]);

        setSubscription(subData);
        setUsage(usageData);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [accessToken]);

  const handleManageBilling = async () => {
    if (!accessToken) return;

    setRedirecting(true);
    setError(null);

    try {
      const { portal_url } = await PaymentAPI.createPortalSession(accessToken);
      window.location.href = portal_url;
    } catch (err: any) {
      console.error('Portal error:', err);
      setError(err.response?.data?.detail || 'Failed to open billing portal');
      setRedirecting(false);
    }
  };

  const getSubscriptionStatusColor = (status: SubscriptionStatus) => {
    switch (status) {
      case SubscriptionStatus.ACTIVE:
      case SubscriptionStatus.TRIALING:
        return 'text-green-700 bg-green-50';
      case SubscriptionStatus.PAST_DUE:
        return 'text-yellow-700 bg-yellow-50';
      case SubscriptionStatus.CANCELED:
      case SubscriptionStatus.UNPAID:
        return 'text-red-700 bg-red-50';
      default:
        return 'text-gray-700 bg-gray-50';
    }
  };

  const getSubscriptionStatusIcon = (status: SubscriptionStatus) => {
    switch (status) {
      case SubscriptionStatus.ACTIVE:
      case SubscriptionStatus.TRIALING:
        return <CheckCircle className="w-5 h-5" />;
      case SubscriptionStatus.PAST_DUE:
        return <Clock className="w-5 h-5" />;
      case SubscriptionStatus.CANCELED:
      case SubscriptionStatus.UNPAID:
        return <XCircle className="w-5 h-5" />;
      default:
        return <AlertCircle className="w-5 h-5" />;
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3">
              <Building2 className="w-8 h-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">Dashboard</span>
            </Link>
            <button
              onClick={logout}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium"
            >
              <LogOut className="w-5 h-5" />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Welcome, {user.full_name || user.email}!
        </h1>

        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-500 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Account Info */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <User className="w-6 h-6 text-blue-600" />
              <h2 className="text-xl font-semibold text-gray-900">Account</h2>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-600">Email</label>
                <p className="font-medium text-gray-900">{user.email}</p>
              </div>
              {user.full_name && (
                <div>
                  <label className="text-sm text-gray-600">Name</label>
                  <p className="font-medium text-gray-900">{user.full_name}</p>
                </div>
              )}
              <div>
                <label className="text-sm text-gray-600">Member Since</label>
                <p className="font-medium text-gray-900">
                  {new Date(user.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>

          {/* Subscription Status */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <CreditCard className="w-6 h-6 text-blue-600" />
              <h2 className="text-xl font-semibold text-gray-900">Subscription</h2>
            </div>
            {subscription ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${getSubscriptionStatusColor(
                      subscription.status
                    )}`}
                  >
                    {getSubscriptionStatusIcon(subscription.status)}
                    {subscription.status.toUpperCase()}
                  </span>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Plan</label>
                  <p className="font-medium text-gray-900 capitalize">
                    {subscription.plan} Plan
                  </p>
                </div>
                {subscription.current_period_end && (
                  <div>
                    <label className="text-sm text-gray-600">
                      {subscription.cancel_at_period_end ? 'Expires' : 'Renews'}
                    </label>
                    <p className="font-medium text-gray-900">
                      {new Date(subscription.current_period_end).toLocaleDateString()}
                    </p>
                  </div>
                )}
                <button
                  onClick={handleManageBilling}
                  disabled={redirecting}
                  className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
                >
                  {redirecting ? 'Opening...' : 'Manage Billing'}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-gray-600 text-sm">No active subscription</p>
                <Link
                  href="/pricing"
                  className="block w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium text-center"
                >
                  Subscribe Now
                </Link>
              </div>
            )}
          </div>

          {/* Usage Stats */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <BarChart3 className="w-6 h-6 text-blue-600" />
              <h2 className="text-xl font-semibold text-gray-900">Usage</h2>
            </div>
            {usage ? (
              <div className="space-y-3">
                <div>
                  <label className="text-sm text-gray-600">Total Analyses</label>
                  <p className="text-3xl font-bold text-gray-900">{usage.total_analyses}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">This Month</label>
                  <p className="text-2xl font-semibold text-gray-900">
                    {usage.analyses_this_month}
                  </p>
                </div>
                {usage.last_analysis && (
                  <div>
                    <label className="text-sm text-gray-600">Last Analysis</label>
                    <p className="font-medium text-gray-900">
                      {new Date(usage.last_analysis).toLocaleDateString()}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-600 text-sm">No usage data available</p>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Link
              href="/"
              className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-blue-600 hover:bg-blue-50 transition-colors"
            >
              <Building2 className="w-6 h-6 text-blue-600" />
              <div>
                <h3 className="font-medium text-gray-900">New Analysis</h3>
                <p className="text-sm text-gray-600">Analyze a parcel</p>
              </div>
            </Link>
            <Link
              href="/pricing"
              className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-blue-600 hover:bg-blue-50 transition-colors"
            >
              <CreditCard className="w-6 h-6 text-blue-600" />
              <div>
                <h3 className="font-medium text-gray-900">Pricing</h3>
                <p className="text-sm text-gray-600">View plans</p>
              </div>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
