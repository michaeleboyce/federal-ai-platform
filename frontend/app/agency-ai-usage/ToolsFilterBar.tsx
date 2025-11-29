'use client';

import type { ProductType } from '@/lib/db/schema';

interface ToolsFilterBarProps {
  selectedType: ProductType | 'all';
  onTypeChange: (type: ProductType | 'all') => void;
  stats: {
    total: number;
    staffChatbot: number;
    codingAssistant: number;
    documentAutomation: number;
  };
}

export default function ToolsFilterBar({
  selectedType,
  onTypeChange,
  stats,
}: ToolsFilterBarProps) {
  const filters: { key: ProductType | 'all'; label: string; count: number; color: string }[] = [
    { key: 'all', label: 'All Tools', count: stats.total, color: 'charcoal' },
    { key: 'staff_chatbot', label: 'Chatbots', count: stats.staffChatbot, color: 'ifp-purple' },
    { key: 'coding_assistant', label: 'Coding Assistants', count: stats.codingAssistant, color: 'ifp-orange' },
    { key: 'document_automation', label: 'Document Automation', count: stats.documentAutomation, color: 'green' },
  ];

  return (
    <div className="flex flex-wrap gap-2 mb-6">
      {filters.map(({ key, label, count, color }) => {
        const isSelected = selectedType === key;

        // Dynamic class based on color
        const baseClasses = 'px-4 py-2 rounded-full text-sm font-medium transition-all border';
        let colorClasses = '';

        if (isSelected) {
          switch (color) {
            case 'ifp-purple':
              colorClasses = 'bg-ifp-purple text-white border-ifp-purple';
              break;
            case 'ifp-orange':
              colorClasses = 'bg-ifp-orange text-white border-ifp-orange';
              break;
            case 'green':
              colorClasses = 'bg-green-600 text-white border-green-600';
              break;
            default:
              colorClasses = 'bg-charcoal text-white border-charcoal';
          }
        } else {
          colorClasses = 'bg-white text-charcoal border-charcoal-300 hover:border-charcoal-400 hover:bg-cream';
        }

        return (
          <button
            key={key}
            onClick={() => onTypeChange(key)}
            className={`${baseClasses} ${colorClasses}`}
          >
            {label}
            <span className={`ml-2 px-1.5 py-0.5 rounded-full text-xs ${
              isSelected ? 'bg-white/20' : 'bg-charcoal-100'
            }`}>
              {count}
            </span>
          </button>
        );
      })}
    </div>
  );
}
