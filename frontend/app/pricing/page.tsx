'use client';

import { useState } from 'react';
import { useAuth, useAccessToken } from '@/lib/auth-context';
import { PaymentAPI } from '@/lib/auth-api';
import { Building2, Check, Zap, FileText, BarChart, MapPin, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function PricingPage() {
  const { user, loading: authLoading } = useAuth();
  const accessToken = useAccessToken();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubscribe = async () => {
    setError(null);

    // Redirect to login if not authenticated
    if (!user || !accessToken) {
      router.push('/auth/login?redirect=/pricing');
      return;
    }

    setLoading(true);

    try {
      const { checkout_url } = await PaymentAPI.createCheckoutSession(accessToken);
      // Redirect to Stripe Checkout
      window.location.href = checkout_url;
    } catch (err: any) {
      console.error('Checkout error:', err);
      setError(err.response?.data?.detail || 'Failed to create checkout session. Please try again.');
      setLoading(false);
    }
  };

  const features = [
    {
      icon: <Zap className="w-5 h-5" />,
      title: 'Unlimited Analyses',
      description: 'Run as many parcel feasibility analyses as you need',
    },
    {
      icon: <FileText className="w-5 h-5" />,
      title: 'PDF Export',
      description: 'Download professional PDF reports for presentations',
    },
    {
      icon: <BarChart className="w-5 h-5" />,
      title: 'Economic Feasibility',
      description: 'Advanced financial modeling and cash flow projections',
    },
    {
      icon: <MapPin className="w-5 h-5" />,
      title: 'All State Laws',
      description: 'SB 9, SB 35, AB 2011, Density Bonus, and more',
    },
    {
      icon: <Building2 className="w-5 h-5" />,
      title: 'New Cities First',
      description: 'Get access to new cities as we expand coverage',
    },
    {
      icon: <Check className="w-5 h-5" />,
      title: 'Priority Support',
      description: 'Fast response times for questions and issues',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3">
              <Building2 className="w-8 h-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">
                Parcel Feasibility Engine
              </span>
            </Link>
            {user ? (
              <Link
                href="/dashboard"
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Dashboard →
              </Link>
            ) : (
              <Link
                href="/auth/login"
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-600">
            Professional housing development analysis for $5/month
          </p>
        </div>

        {error && (
          <div className="mb-8 bg-red-50 border-l-4 border-red-500 rounded-lg p-4 max-w-2xl mx-auto">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-900 mb-1">Payment Error</h3>
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Pricing Card */}
        <div className="bg-white rounded-2xl shadow-lg border-2 border-blue-600 p-8 mb-12">
          <div className="text-center mb-8">
            <div className="inline-block bg-blue-100 text-blue-700 px-4 py-1 rounded-full text-sm font-semibold mb-4">
              PRO PLAN
            </div>
            <div className="flex items-baseline justify-center gap-2 mb-2">
              <span className="text-5xl font-bold text-gray-900">$5</span>
              <span className="text-xl text-gray-600">/month</span>
            </div>
            <p className="text-gray-600">Cancel anytime. No hidden fees.</p>
          </div>

          <button
            onClick={handleSubscribe}
            disabled={loading || authLoading}
            className="w-full bg-blue-600 text-white py-4 rounded-lg hover:bg-blue-700 transition-colors font-medium text-lg disabled:opacity-50 disabled:cursor-not-allowed mb-8"
          >
            {loading
              ? 'Redirecting to checkout...'
              : user
              ? 'Subscribe Now'
              : 'Sign Up to Subscribe'}
          </button>

          <div className="space-y-4">
            {features.map((feature, index) => (
              <div key={index} className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
                  {feature.icon}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{feature.title}</h3>
                  <p className="text-sm text-gray-600">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* FAQ */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Frequently Asked Questions
          </h2>

          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                What do you use my subscription for?
              </h3>
              <p className="text-gray-600 text-sm">
                Your subscription supports expanding to new cities, maintaining accurate
                legal updates, and improving the platform. We're committed to providing
                the best housing development analysis tool in California.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                Can I cancel anytime?
              </h3>
              <p className="text-gray-600 text-sm">
                Yes! You can cancel your subscription at any time from your dashboard.
                You'll retain access until the end of your current billing period.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                Do you offer refunds?
              </h3>
              <p className="text-gray-600 text-sm">
                We offer a 7-day money-back guarantee. If you're not satisfied within
                the first week, contact us for a full refund.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                What cities do you currently support?
              </h3>
              <p className="text-gray-600 text-sm">
                We currently support Santa Monica with deep integration of local zoning
                codes and special plan areas. More California cities coming soon!
              </p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-12 text-center">
          <p className="text-gray-600 mb-4">
            Have questions? <a href="mailto:support@example.com" className="text-blue-600 hover:text-blue-700">Contact us</a>
          </p>
          <Link
            href="/"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            ← Back to Home
          </Link>
        </div>
      </main>
    </div>
  );
}
