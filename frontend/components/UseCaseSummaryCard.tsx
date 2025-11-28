import Link from 'next/link';
import type { UseCase } from '@/lib/use-case-db';

interface UseCaseSummaryCardProps {
  useCase: UseCase;
}

export default function UseCaseSummaryCard({ useCase }: UseCaseSummaryCardProps) {
  // Get AI type badges
  const getAITypeBadges = () => {
    const badges = [];

    if (useCase.genaiFlag) {
      badges.push(
        <span key="genai" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ifp-orange-light text-ifp-orange-dark border border-ifp-orange">
          GenAI
        </span>
      );
    }
    if (useCase.hasLlm) {
      badges.push(
        <span key="llm" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-charcoal-100 text-charcoal-700 border border-charcoal-400">
          LLM
        </span>
      );
    }
    if (useCase.hasChatbot) {
      badges.push(
        <span key="chatbot" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple">
          Chatbot
        </span>
      );
    }
    if (useCase.hasClassicMl) {
      badges.push(
        <span key="ml" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-charcoal-200 text-charcoal-700 border border-charcoal-400">
          ML
        </span>
      );
    }

    return badges.length > 0 ? badges : [
      <span key="other" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-charcoal-100 text-charcoal-600 border border-charcoal-300">
        Other AI
      </span>
    ];
  };

  // Truncate purpose text
  const truncatePurpose = (text: string | null, maxLength: number = 150): string => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  };

  return (
    <Link
      href={`/use-cases/${useCase.slug}`}
      className="block bg-white border border-charcoal-200 rounded-lg p-4 hover:border-ifp-purple hover:shadow-md transition-all"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <h3 className="font-semibold text-charcoal text-sm line-clamp-2 flex-1">
          {useCase.useCaseName}
        </h3>
        <svg
          className="w-5 h-5 text-ifp-purple flex-shrink-0 ml-2"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </div>

      {/* Bureau */}
      {useCase.bureau && (
        <div className="text-xs text-charcoal-500 mb-2">{useCase.bureau}</div>
      )}

      {/* Domain & Stage */}
      <div className="flex flex-wrap gap-2 mb-3">
        {useCase.domainCategory && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-charcoal-100 text-charcoal-700">
            {useCase.domainCategory}
          </span>
        )}
        {useCase.stageOfDevelopment && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-charcoal-50 text-charcoal-600">
            {useCase.stageOfDevelopment}
          </span>
        )}
      </div>

      {/* AI Type Badges */}
      <div className="flex flex-wrap gap-1 mb-3">
        {getAITypeBadges()}
      </div>

      {/* Purpose (truncated) */}
      {useCase.intendedPurpose && (
        <p className="text-xs text-charcoal-500 leading-relaxed">
          {truncatePurpose(useCase.intendedPurpose)}
        </p>
      )}

      {/* Implementation Date */}
      {useCase.dateImplemented && (
        <div className="mt-3 text-xs text-charcoal-400">
          Implemented: {useCase.dateImplemented}
        </div>
      )}
    </Link>
  );
}
