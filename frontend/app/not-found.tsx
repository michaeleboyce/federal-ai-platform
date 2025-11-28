import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-cream flex items-center justify-center">
      <div className="bg-white rounded-lg border border-charcoal-200 p-8 max-w-md text-center">
        <div className="text-6xl mb-4">404</div>
        <h1 className="font-serif text-2xl font-medium text-charcoal mb-2">
          Page Not Found
        </h1>
        <p className="text-charcoal-500 mb-6">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link
          href="/"
          className="inline-flex items-center px-4 py-2 bg-ifp-purple text-white rounded-md hover:bg-ifp-purple-dark transition-colors"
        >
          Return to Home
        </Link>
      </div>
    </div>
  );
}
