'use client';

import { useState } from 'react';

export default function SentryExamplePage() {
  const [error, setError] = useState<string | null>(null);

  const triggerError = () => {
    try {
      // This will throw a ReferenceError
      // @ts-ignore - Intentionally calling undefined function
      myUndefinedFunction();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      throw err; // Re-throw to let Sentry capture it
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Sentry Error Testing Page
        </h1>

        <p className="text-gray-600 mb-6">
          Click the button below to trigger a test error. If Sentry is configured correctly,
          this error will be captured and sent to your Sentry project.
        </p>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">
            What happens when you click:
          </h2>
          <ul className="list-disc list-inside text-blue-800 space-y-1">
            <li>A ReferenceError will be thrown (calling undefined function)</li>
            <li>Sentry will capture the error with full stack trace</li>
            <li>The error will appear in your Sentry dashboard</li>
            <li>Session replay will be recorded (if enabled)</li>
          </ul>
        </div>

        <button
          onClick={triggerError}
          className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
        >
          Trigger Test Error
        </button>

        {error && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="text-red-900 font-semibold mb-2">Error Triggered:</h3>
            <code className="text-red-800 text-sm">{error}</code>
            <p className="text-red-700 text-sm mt-2">
              Check your browser console and Sentry dashboard for the captured error.
            </p>
          </div>
        )}

        <div className="mt-8 border-t pt-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">
            Testing Checklist:
          </h2>
          <ol className="list-decimal list-inside text-gray-700 space-y-2">
            <li>Ensure NEXT_PUBLIC_SENTRY_DSN is set in your .env.local</li>
            <li>Click the "Trigger Test Error" button above</li>
            <li>Open your browser's developer console (F12)</li>
            <li>Look for the error message</li>
            <li>Visit your Sentry dashboard to see the captured error</li>
          </ol>
        </div>

        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 text-sm">
            <strong>Note:</strong> In development mode, errors are logged to console but not sent to Sentry
            (based on the beforeSend configuration). Deploy to production or temporarily modify the
            beforeSend function to test in development.
          </p>
        </div>
      </div>
    </div>
  );
}
