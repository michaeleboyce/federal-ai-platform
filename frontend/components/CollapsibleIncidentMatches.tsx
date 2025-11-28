'use client';

import { useState } from 'react';
import Link from 'next/link';

interface IncidentMatch {
  incidentId: number;
  title: string;
  description?: string | null;
  date?: string | null;
  similarityScore: number;
  matchSource: 'semantic' | 'text' | 'hybrid';
  hasDataLeak?: boolean;
  hasCyberAttack?: boolean;
  hasLlm?: boolean;
}

interface CollapsibleIncidentMatchesProps {
  incidents: IncidentMatch[];
  highThreshold?: number;
  lowThreshold?: number;
}

const HIGH_THRESHOLD = 0.75;
const LOW_THRESHOLD = 0.60;

export default function CollapsibleIncidentMatches({
  incidents,
  highThreshold = HIGH_THRESHOLD,
  lowThreshold = LOW_THRESHOLD,
}: CollapsibleIncidentMatchesProps) {
  const [showMore, setShowMore] = useState(false);

  // Split incidents into tiers
  const primaryMatches = incidents.filter((i) => i.similarityScore >= highThreshold);
  const secondaryMatches = incidents.filter(
    (i) => i.similarityScore >= lowThreshold && i.similarityScore < highThreshold
  );

  const totalVisible = primaryMatches.length + (showMore ? secondaryMatches.length : 0);

  if (incidents.length === 0) {
    return (
      <p className="text-sm text-gov-slate-500">No related AI incidents found.</p>
    );
  }

  const renderIncidentCard = (incident: IncidentMatch) => (
    <Link
      key={incident.incidentId}
      href={`/incidents/${incident.incidentId}`}
      className="block p-4 bg-gov-slate-50 hover:bg-gov-slate-100 rounded-lg border border-gov-slate-200 transition-colors"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gov-navy-900 text-sm line-clamp-2">
            {incident.title}
          </h3>
          {incident.date && (
            <p className="text-xs text-gov-slate-500 mt-1">{incident.date}</p>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          {/* Match quality indicator */}
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded ${
              incident.similarityScore >= 0.8
                ? 'bg-status-success-light text-status-success-dark border border-status-success'
                : incident.similarityScore >= 0.7
                ? 'bg-status-warning-light text-status-warning-dark border border-status-warning'
                : 'bg-gov-slate-100 text-gov-slate-600 border border-gov-slate-300'
            }`}
          >
            {Math.round(incident.similarityScore * 100)}% match
          </span>
          {/* Risk indicators */}
          <div className="flex gap-1">
            {incident.hasDataLeak && (
              <span
                className="text-xs px-1.5 py-0.5 bg-red-100 text-red-700 rounded"
                title="Data Leak"
              >
                Leak
              </span>
            )}
            {incident.hasCyberAttack && (
              <span
                className="text-xs px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded"
                title="Cyber Attack"
              >
                Attack
              </span>
            )}
            {incident.hasLlm && (
              <span
                className="text-xs px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded"
                title="LLM/Chatbot"
              >
                LLM
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );

  return (
    <div className="space-y-3">
      {/* Primary matches - always visible */}
      {primaryMatches.map(renderIncidentCard)}

      {/* Secondary matches - collapsed by default */}
      {showMore && secondaryMatches.map(renderIncidentCard)}

      {/* Show more/less toggle */}
      {secondaryMatches.length > 0 && (
        <button
          onClick={() => setShowMore(!showMore)}
          className="w-full py-2 px-4 text-sm font-medium text-gov-navy-700 hover:text-gov-navy-900 bg-gov-slate-100 hover:bg-gov-slate-200 rounded-lg border border-gov-slate-300 transition-colors flex items-center justify-center gap-2"
        >
          {showMore ? (
            <>
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 15l7-7 7 7"
                />
              </svg>
              Show less
            </>
          ) : (
            <>
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
              Show {secondaryMatches.length} more related incident
              {secondaryMatches.length > 1 ? 's' : ''} ({Math.round(lowThreshold * 100)}-
              {Math.round(highThreshold * 100)}% match)
            </>
          )}
        </button>
      )}

      {/* Summary when there are no high-confidence matches */}
      {primaryMatches.length === 0 && secondaryMatches.length > 0 && !showMore && (
        <p className="text-xs text-gov-slate-500 text-center">
          No high-confidence matches. Click above to see {secondaryMatches.length} moderate match
          {secondaryMatches.length > 1 ? 'es' : ''}.
        </p>
      )}
    </div>
  );
}
