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
        <span key="genai" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ai-teal-light text-ai-teal-dark border border-ai-teal">
          GenAI
        </span>
      );
    }
    if (useCase.hasLlm) {
      badges.push(
        <span key="llm" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ai-indigo-light text-ai-indigo-dark border border-ai-indigo">
          LLM
        </span>
      );
    }
    if (useCase.hasChatbot) {
      badges.push(
        <span key="chatbot" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ai-blue-light text-ai-blue-dark border border-ai-blue">
          Chatbot
        </span>
      );
    }
    if (useCase.hasClassicMl) {
      badges.push(
        <span key="ml" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gov-slate-200 text-gov-slate-700 border border-gov-slate-400">
          ML
        </span>
      );
    }

    return badges.length > 0 ? badges : [
      <span key="other" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gov-slate-100 text-gov-slate-600 border border-gov-slate-300">
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
      className="block bg-white border border-gov-slate-200 rounded-lg p-4 hover:border-gov-navy-600 hover:shadow-md transition-all"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <h3 className="font-semibold text-gov-navy-900 text-sm line-clamp-2 flex-1">
          {useCase.useCaseName}
        </h3>
        <svg
          className="w-5 h-5 text-gov-navy-600 flex-shrink-0 ml-2"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </div>

      {/* Bureau */}
      {useCase.bureau && (
        <div className="text-xs text-gov-slate-600 mb-2">{useCase.bureau}</div>
      )}

      {/* Domain & Stage */}
      <div className="flex flex-wrap gap-2 mb-3">
        {useCase.domainCategory && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gov-navy-100 text-gov-navy-800">
            {useCase.domainCategory}
          </span>
        )}
        {useCase.stageOfDevelopment && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gov-slate-100 text-gov-slate-700">
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
        <p className="text-xs text-gov-slate-600 leading-relaxed">
          {truncatePurpose(useCase.intendedPurpose)}
        </p>
      )}

      {/* Implementation Date */}
      {useCase.dateImplemented && (
        <div className="mt-3 text-xs text-gov-slate-500">
          Implemented: {useCase.dateImplemented}
        </div>
      )}
    </Link>
  );
}
