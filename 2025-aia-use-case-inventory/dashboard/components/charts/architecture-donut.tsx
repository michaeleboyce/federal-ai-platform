/**
 * Architecture-type donut chart. Thin wrapper around the shared DonutChart
 * that centralizes the color map and humanized labels for the
 * `tag.architecture_type` enum.
 */

"use client";

import { DonutChart, type DonutDatum } from "./donut-chart";

const ARCHITECTURE_COLORS: Record<string, string> = {
  inference_only: "#3b82f6", // blue-500
  rag_pipeline: "#8b5cf6", // violet-500
  fine_tuned: "#f59e0b", // amber-500
  custom_trained: "#10b981", // emerald-500
  agentic_workflow: "#ef4444", // red-500
  unknown: "#94a3b8", // slate-400
};

const ARCHITECTURE_LABELS: Record<string, string> = {
  inference_only: "Inference only",
  rag_pipeline: "RAG pipeline",
  fine_tuned: "Fine-tuned",
  custom_trained: "Custom trained",
  agentic_workflow: "Agentic workflow",
  unknown: "Unknown",
};

export function ArchitectureDonut({ data }: { data: DonutDatum[] }) {
  return (
    <DonutChart
      data={data}
      colorMap={ARCHITECTURE_COLORS}
      labelMap={ARCHITECTURE_LABELS}
      centerSubLabel="use cases"
      height={280}
    />
  );
}

const LLM_VENDOR_COLORS: Record<string, string> = {
  Microsoft: "#2563eb",
  OpenAI: "#10b981",
  Anthropic: "#f59e0b",
  Google: "#ef4444",
  Amazon: "#f97316",
  Other: "#94a3b8",
};

export function LLMVendorDonut({ data }: { data: DonutDatum[] }) {
  return (
    <DonutChart
      data={data}
      colorMap={LLM_VENDOR_COLORS}
      centerSubLabel="general-LLM entries"
      height={280}
    />
  );
}
