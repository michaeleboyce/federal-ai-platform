/**
 * Renders a use case's analytical tags as a two-column hanging-indent
 * definition list in the editorial aesthetic. Each row pairs a field
 * name + short explanation (hanging indent) with the raw value
 * (right-aligned, monospace).
 *
 * Server-renderable (no client state).
 */

import type { UseCaseTag } from "@/lib/types";
import { formatBoolFlag } from "@/lib/formatting";

interface TagSpec {
  key: keyof UseCaseTag;
  label: string;
  explanation: string;
  kind: "text" | "bool";
}

const SPECS: TagSpec[] = [
  {
    key: "entry_type",
    label: "Entry type",
    explanation:
      "Shape of the reported entry: a custom-built system, a deployment of a product, a bespoke application, a generic-use pattern, or a product feature.",
    kind: "text",
  },
  {
    key: "is_product_capability_entry",
    label: "Product capability entry",
    explanation:
      "Whether this entry describes a capability of a commercial product rather than a distinct system.",
    kind: "bool",
  },
  {
    key: "product_capability",
    label: "Product capability",
    explanation: "Named capability inside the product, if applicable.",
    kind: "text",
  },
  {
    key: "is_general_llm_access",
    label: "General LLM access",
    explanation: "Marks enterprise-wide ChatGPT-style access programs.",
    kind: "bool",
  },
  {
    key: "is_coding_tool",
    label: "Coding tool",
    explanation:
      "AI-assisted code generation / completion tools (Copilot, Cursor, etc.).",
    kind: "bool",
  },
  {
    key: "is_cots_commercial",
    label: "COTS / commercial",
    explanation: "Commercial off-the-shelf deployment.",
    kind: "bool",
  },
  {
    key: "tool_product_name",
    label: "Tool / product name",
    explanation: "Tool or product name as parsed from the narrative.",
    kind: "text",
  },
  {
    key: "tool_vendor",
    label: "Tool vendor",
    explanation: "Vendor behind the tool.",
    kind: "text",
  },
  {
    key: "ai_sophistication",
    label: "AI sophistication",
    explanation:
      "Classification: general LLM, coding assistant, agentic, classical ML, computer vision, NLP, or predictive analytics.",
    kind: "text",
  },
  {
    key: "is_generative_ai",
    label: "Generative AI",
    explanation: "Flagged when the entry is a generative AI system.",
    kind: "bool",
  },
  {
    key: "is_frontier_model",
    label: "Frontier model",
    explanation: "Uses a frontier LLM (GPT-4, Claude 3+, Gemini 1.5+, etc.).",
    kind: "bool",
  },
  {
    key: "deployment_scope",
    label: "Deployment scope",
    explanation: "Enterprise-wide, department, bureau, office, team, or pilot.",
    kind: "text",
  },
  {
    key: "scope_detail",
    label: "Scope detail",
    explanation: "Free-text elaboration on the scope.",
    kind: "text",
  },
  {
    key: "is_enterprise_wide",
    label: "Enterprise-wide",
    explanation: "Available across the whole agency.",
    kind: "bool",
  },
  {
    key: "estimated_user_count",
    label: "Estimated users",
    explanation: "Rough headcount if reported.",
    kind: "text",
  },
  {
    key: "architecture_type",
    label: "Architecture",
    explanation:
      "Implementation pattern: inference-only, RAG pipeline, fine-tuned, custom-trained, or an agentic workflow.",
    kind: "text",
  },
  {
    key: "has_model_training",
    label: "Involves model training",
    explanation: "Agency trains or fine-tunes a model in-house.",
    kind: "bool",
  },
  {
    key: "cots_product_name",
    label: "COTS product",
    explanation: "Commercial-off-the-shelf product name.",
    kind: "text",
  },
  {
    key: "cots_vendor",
    label: "COTS vendor",
    explanation: "Vendor of the COTS product.",
    kind: "text",
  },
  {
    key: "is_microsoft_copilot",
    label: "Microsoft Copilot",
    explanation: "Uses Microsoft Copilot family.",
    kind: "bool",
  },
  {
    key: "is_openai",
    label: "OpenAI",
    explanation: "Uses OpenAI models or APIs.",
    kind: "bool",
  },
  {
    key: "is_anthropic",
    label: "Anthropic",
    explanation: "Uses Anthropic models or APIs.",
    kind: "bool",
  },
  {
    key: "is_google",
    label: "Google AI",
    explanation: "Uses Google/Gemini models or APIs.",
    kind: "bool",
  },
  {
    key: "is_github_copilot",
    label: "GitHub Copilot",
    explanation: "Uses GitHub Copilot.",
    kind: "bool",
  },
  {
    key: "is_aws_ai",
    label: "AWS AI",
    explanation: "Uses AWS Bedrock, SageMaker, or related services.",
    kind: "bool",
  },
  {
    key: "use_type",
    label: "Use type",
    explanation:
      "Mission-critical, administrative, IT operations, cybersecurity, or research.",
    kind: "text",
  },
  {
    key: "is_public_facing",
    label: "Public-facing",
    explanation: "The system interacts with the public, not just employees.",
    kind: "bool",
  },
  {
    key: "has_meaningful_risk_docs",
    label: "Meaningful risk docs",
    explanation:
      "Risk-management fields include substantive content beyond boilerplate.",
    kind: "bool",
  },
  {
    key: "high_impact_designation",
    label: "High-impact designation",
    explanation: "M-25-21 high-impact classification.",
    kind: "text",
  },
  {
    key: "deployment_environment",
    label: "Deployment environment",
    explanation: "Cloud / on-premises / hybrid context if parseable.",
    kind: "text",
  },
  {
    key: "has_ato_or_fedramp",
    label: "ATO / FedRAMP",
    explanation: "Has an Authority to Operate or FedRAMP authorization.",
    kind: "bool",
  },
];

export function TagDefinitionList({ tags }: { tags: UseCaseTag | null }) {
  if (!tags) {
    return (
      <p className="text-sm text-muted-foreground">
        No analytical tags are available for this entry.
      </p>
    );
  }
  return (
    <dl className="border-t-2 border-foreground">
      {SPECS.map((spec) => {
        const raw = tags[spec.key] as number | string | null | undefined;
        const isEmpty =
          raw == null ||
          raw === "" ||
          (spec.kind === "bool" && raw !== 0 && raw !== 1);
        const displayValue = isEmpty
          ? "—"
          : spec.kind === "bool"
            ? formatBoolFlag(raw as number)
            : String(raw);
        return (
          <div
            key={String(spec.key)}
            className="grid grid-cols-1 gap-1 border-b border-border py-3 sm:grid-cols-[240px,1fr,auto] sm:items-baseline sm:gap-6"
          >
            <dt className="flex flex-col">
              <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-foreground">
                {spec.label}
              </span>
            </dt>
            <dd className="text-[12.5px] leading-snug text-muted-foreground">
              {spec.explanation}
            </dd>
            <dd
              className={
                "font-mono text-[11px] uppercase tracking-[0.08em] sm:text-right " +
                (isEmpty ? "text-muted-foreground" : "text-foreground")
              }
            >
              {displayValue}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}
