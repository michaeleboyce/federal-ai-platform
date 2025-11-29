'use client';

import { List, GitBranch, Layers } from 'lucide-react';

export type ViewMode = 'list' | 'tree' | 'grouped';

interface ViewModeOption {
  mode: ViewMode;
  label: string;
  icon: typeof List;
  description: string;
}

const viewModeOptions: ViewModeOption[] = [
  {
    mode: 'list',
    label: 'List',
    icon: List,
    description: 'Flat list view',
  },
  {
    mode: 'tree',
    label: 'Tree',
    icon: GitBranch,
    description: 'Hierarchical tree view',
  },
  {
    mode: 'grouped',
    label: 'Grouped',
    icon: Layers,
    description: 'Grouped by parent agency',
  },
];

export interface ViewModeToggleProps {
  currentMode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
  availableModes?: ViewMode[];
  size?: 'sm' | 'md';
  className?: string;
}

export function ViewModeToggle({
  currentMode,
  onModeChange,
  availableModes = ['list', 'tree', 'grouped'],
  size = 'md',
  className = '',
}: ViewModeToggleProps) {
  const filteredOptions = viewModeOptions.filter((opt) =>
    availableModes.includes(opt.mode)
  );

  const sizeClasses = {
    sm: {
      container: 'gap-0.5',
      button: 'px-2 py-1 text-xs',
      icon: 'w-3.5 h-3.5',
    },
    md: {
      container: 'gap-1',
      button: 'px-3 py-1.5 text-sm',
      icon: 'w-4 h-4',
    },
  };

  const classes = sizeClasses[size];

  return (
    <div
      className={`inline-flex items-center bg-slate-100 rounded-lg p-0.5 ${classes.container} ${className}`}
    >
      {filteredOptions.map((option) => {
        const Icon = option.icon;
        const isActive = currentMode === option.mode;

        return (
          <button
            key={option.mode}
            onClick={() => onModeChange(option.mode)}
            title={option.description}
            className={`
              flex items-center gap-1.5 ${classes.button} rounded-md font-medium
              transition-all duration-150
              ${
                isActive
                  ? 'bg-white text-ai-blue shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }
            `}
          >
            <Icon className={classes.icon} />
            <span>{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}

export default ViewModeToggle;
