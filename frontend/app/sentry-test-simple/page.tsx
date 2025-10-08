'use client';

import * as Sentry from '@sentry/nextjs';
import { useEffect, useState } from 'react';

export default function SentryTestSimple() {
  const [dsn, setDsn] = useState<string>('');
  const [sentryReady, setSentryReady] = useState(false);
  const [messageSent, setMessageSent] = useState(false);
  const [errorSent, setErrorSent] = useState(false);

  useEffect(() => {
    // Check if Sentry is initialized
    const client = Sentry.getClient();
    if (client) {
      setSentryReady(true);
      const options = client.getOptions();
      setDsn(options.dsn || 'No DSN found');
    }
  }, []);

  const sendTestMessage = () => {
    console.log('Sending test message to Sentry...');
    Sentry.captureMessage('Test message from frontend Sentry test page', 'info');
    setMessageSent(true);
    alert('Test message sent! Check browser console and Sentry dashboard.');
  };

  const sendTestError = () => {
    console.log('Sending test error to Sentry...');
    try {
      throw new Error('Test error from frontend Sentry test page');
    } catch (error) {
      Sentry.captureException(error);
      setErrorSent(true);
      alert('Test error sent! Check browser console and Sentry dashboard.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Sentry Integration Test</h1>

        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Sentry Status</h2>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="font-medium">Sentry Client:</span>
              <span className={sentryReady ? 'text-green-600' : 'text-red-600'}>
                {sentryReady ? '✅ Initialized' : '❌ Not Initialized'}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="font-medium">DSN:</span>
              <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                {dsn || 'Loading...'}
              </code>
            </div>

            <div className="flex items-center gap-2">
              <span className="font-medium">Environment:</span>
              <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                {process.env.NODE_ENV}
              </code>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Send Test Events</h2>

          <div className="space-y-4">
            <div>
              <button
                onClick={sendTestMessage}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold mr-4"
              >
                Send Test Message
              </button>
              {messageSent && <span className="text-green-600">✅ Message sent</span>}
            </div>

            <div>
              <button
                onClick={sendTestError}
                className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-semibold mr-4"
              >
                Send Test Error
              </button>
              {errorSent && <span className="text-green-600">✅ Error sent</span>}
            </div>
          </div>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="font-semibold text-yellow-900 mb-2">Instructions:</h3>
          <ol className="list-decimal list-inside text-yellow-800 space-y-1">
            <li>Verify Sentry Client is initialized above</li>
            <li>Click "Send Test Message" or "Send Test Error"</li>
            <li>Open browser console (F12) to see logs</li>
            <li>Check Sentry dashboard for the event</li>
            <li>Events should appear within 10-30 seconds</li>
          </ol>
        </div>

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">Sentry Dashboard:</h3>
          <a
            href="https://sentry.io/organizations/d3ai/issues/?project=4510151500496896"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            View Frontend Issues →
          </a>
        </div>
      </div>
    </div>
  );
}
