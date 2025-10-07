'use client';

import { Building2, Zap, MapPin, FileText, Calculator, Home, TrendingUp, CheckCircle, ArrowRight, BarChart3, Shield } from 'lucide-react';
import Link from 'next/link';

export default function LandingPage() {
  const features = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: 'Instant Feasibility Analysis',
      description: 'Analyze parcels in seconds with SB 9, SB 35, AB 2011, and Density Bonus law integration',
    },
    {
      icon: <MapPin className="w-6 h-6" />,
      title: 'GIS Integration',
      description: 'Interactive map with automatic parcel data from Santa Monica GIS services',
    },
    {
      icon: <FileText className="w-6 h-6" />,
      title: 'Export PDF Reports',
      description: 'Professional reports ready for clients, lenders, and city planning departments',
    },
    {
      icon: <Calculator className="w-6 h-6" />,
      title: 'Affordable Housing Calculations',
      description: 'Automatic affordable unit requirements and density bonus calculations',
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: 'Economic Feasibility',
      description: 'Advanced financial modeling with NPV, IRR, and cash flow projections',
    },
    {
      icon: <BarChart3 className="w-6 h-6" />,
      title: 'Real-time Zoning Analysis',
      description: 'Base zoning, overlays, and special plan area analysis for accurate results',
    },
  ];

  const benefits = [
    'SB 9 lot split and duplex analysis',
    'SB 35 streamlined approval pathways',
    'AB 2011 affordable housing on commercial sites',
    'Density Bonus concessions and waivers',
    'Parking requirement calculations (including AB 2097)',
    'Height, setback, and FAR analysis',
    'Environmental overlay checks',
    'Multi-parcel combination support',
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Building2 className="w-8 h-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">
                Parcel Feasibility Engine
              </span>
            </div>
            <div className="flex items-center gap-4">
              <Link
                href="/pricing"
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                Pricing
              </Link>
              <Link
                href="/auth/login"
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                Sign In
              </Link>
              <Link
                href="/auth/register"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Get Started Free
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            California Housing Development Made{' '}
            <span className="text-blue-600">Simple</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-8">
            AI-powered feasibility analysis with state housing law integration.
            Analyze parcels in seconds, not hours.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              href="/auth/register"
              className="px-8 py-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 text-lg shadow-lg"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/auth/login"
              className="px-8 py-4 bg-white text-gray-700 border-2 border-gray-300 font-semibold rounded-lg hover:bg-gray-50 transition-colors text-lg"
            >
              Sign In
            </Link>
          </div>
          <div className="mt-6 flex items-center justify-center gap-2 text-gray-600">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <span className="font-medium">3 free analyses per month</span>
            <span className="text-gray-400">•</span>
            <span>No credit card required</span>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Everything You Need for Development Analysis
          </h2>
          <p className="text-xl text-gray-600">
            Comprehensive tools for developers, planners, and policymakers
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow"
            >
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600 mb-4">
                {feature.icon}
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-white border-t border-b border-gray-200 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600">
              Start analyzing in 3 simple steps
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                1
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Create Free Account
              </h3>
              <p className="text-gray-600">
                Sign up in seconds with just your email. No credit card required to start.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                2
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Analyze Up to 3 Parcels
              </h3>
              <p className="text-gray-600">
                Select parcels from the map or enter manually. Get instant feasibility results.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                3
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Subscribe for Unlimited
              </h3>
              <p className="text-gray-600">
                Upgrade to the Pro plan for just $5/month and unlock unlimited analyses.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* State Laws Coverage */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-block bg-blue-100 text-blue-700 px-4 py-1 rounded-full text-sm font-semibold mb-4">
              CALIFORNIA HOUSING LAWS
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              Comprehensive State Law Integration
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              Our platform analyzes every applicable California housing law to maximize
              your development potential. We stay up-to-date with the latest regulations
              so you don't have to.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{benefit}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-8">
            <div className="space-y-6">
              <div className="border-l-4 border-blue-600 pl-4">
                <h3 className="font-semibold text-gray-900 mb-1">SB 9 (2021)</h3>
                <p className="text-sm text-gray-600">
                  Urban lot splits and duplex development - up to 4 units total
                </p>
              </div>
              <div className="border-l-4 border-green-600 pl-4">
                <h3 className="font-semibold text-gray-900 mb-1">SB 35 (2017)</h3>
                <p className="text-sm text-gray-600">
                  Streamlined ministerial approval for affordable housing
                </p>
              </div>
              <div className="border-l-4 border-purple-600 pl-4">
                <h3 className="font-semibold text-gray-900 mb-1">AB 2011 (2022)</h3>
                <p className="text-sm text-gray-600">
                  100% affordable housing on commercial and parking sites
                </p>
              </div>
              <div className="border-l-4 border-orange-600 pl-4">
                <h3 className="font-semibold text-gray-900 mb-1">Density Bonus Law</h3>
                <p className="text-sm text-gray-600">
                  Up to 80% density increase plus concessions and waivers
                </p>
              </div>
              <div className="border-l-4 border-teal-600 pl-4">
                <h3 className="font-semibold text-gray-900 mb-1">AB 2097 (2022)</h3>
                <p className="text-sm text-gray-600">
                  Parking minimum elimination near major transit stops
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Teaser */}
      <section className="bg-blue-600 py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Affordable, Transparent Pricing
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Start with 3 free analyses per month. Upgrade to unlimited for just $5/month.
          </p>
          <div className="bg-white rounded-lg p-8 inline-block">
            <div className="flex items-baseline justify-center gap-2 mb-4">
              <span className="text-5xl font-bold text-gray-900">$5</span>
              <span className="text-xl text-gray-600">/month</span>
            </div>
            <ul className="text-left space-y-2 mb-6">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                <span className="text-gray-700">Unlimited analyses</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                <span className="text-gray-700">PDF export</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                <span className="text-gray-700">Economic feasibility modeling</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                <span className="text-gray-700">Priority support</span>
              </li>
            </ul>
            <Link
              href="/pricing"
              className="block w-full px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              View Full Pricing
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-12 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Start Analyzing?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join developers, planners, and policymakers using our platform
          </p>
          <Link
            href="/auth/register"
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-blue-600 font-semibold rounded-lg hover:bg-gray-100 transition-colors text-lg shadow-lg"
          >
            Get Started Free
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Building2 className="w-6 h-6 text-blue-600" />
                <span className="font-bold text-gray-900">Parcel Feasibility Engine</span>
              </div>
              <p className="text-gray-600 text-sm">
                AI-powered California housing development analysis with state law integration.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Product</h3>
              <ul className="space-y-2">
                <li>
                  <Link href="/pricing" className="text-gray-600 hover:text-gray-900">
                    Pricing
                  </Link>
                </li>
                <li>
                  <Link href="/auth/login" className="text-gray-600 hover:text-gray-900">
                    Sign In
                  </Link>
                </li>
                <li>
                  <Link href="/auth/register" className="text-gray-600 hover:text-gray-900">
                    Register
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Legal</h3>
              <p className="text-sm text-gray-600 mb-2">
                <strong>Disclaimer:</strong> This tool provides analysis for informational
                purposes only and does not constitute legal advice.
              </p>
              <p className="text-sm text-gray-600">
                Always consult with qualified attorneys, architects, and local planning
                departments before making development decisions.
              </p>
            </div>
          </div>
          <div className="border-t border-gray-200 pt-8 text-center text-gray-600 text-sm">
            <p>© 2025 Parcel Feasibility Engine. Built with FastAPI + Next.js.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
