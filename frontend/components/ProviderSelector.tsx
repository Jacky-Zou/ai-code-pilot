"use client";

import { Bot, Check, Cpu, Lock } from "lucide-react";
import { useMemo, useState } from "react";
import type { ProviderName } from "@/lib/api";

export type Language = "en";

type ModelOption = {
  id: string;
  name: string;
  provider: ProviderName;
  providerLabel: string;
  model: string;
  description: string;
  status: "available" | "coming-soon";
};

// The catalog intentionally includes planned providers so the UI communicates
// the product direction without allowing unsupported backend calls. Only rows
// marked as available can be selected and sent through the API client today.
const MODEL_CATALOG: ModelOption[] = [
  {
    id: "deepseek-v4-pro",
    name: "DeepSeek V4-Pro",
    provider: "deepseek",
    providerLabel: "DeepSeek",
    model: "deepseek-v4-pro",
    description: "Default coding model for repository analysis and tool calling.",
    status: "available"
  },
  {
    id: "gpt-5-2",
    name: "GPT-5.2",
    provider: "openai",
    providerLabel: "OpenAI",
    model: "gpt-5.2",
    description: "OpenAI coding model option for agentic workflows.",
    status: "available"
  },
  {
    id: "glm-4-6",
    name: "GLM-4.6",
    provider: "zhipu",
    providerLabel: "Zhipu GLM",
    model: "glm-4.6",
    description: "Planned long-context Chinese engineering provider.",
    status: "coming-soon"
  },
  {
    id: "qwen-coder",
    name: "Qwen Coder",
    provider: "qwen",
    providerLabel: "Qwen",
    model: "qwen-coder-latest",
    description: "Planned coding provider for generation and refactoring.",
    status: "coming-soon"
  },
  {
    id: "claude-sonnet",
    name: "Claude Sonnet",
    provider: "claude",
    providerLabel: "Anthropic",
    model: "claude-sonnet-latest",
    description: "Planned provider for review and architecture analysis.",
    status: "coming-soon"
  }
];

const PROVIDERS = Array.from(
  new Map(MODEL_CATALOG.map((model) => [model.provider, model.providerLabel])).entries()
).map(([provider, label]) => ({ provider: provider as ProviderName, label }));

export interface ProviderSelection {
  provider: ProviderName;
  model: string;
}

export interface ProviderSelectorProps {
  language?: Language;
  value?: ProviderSelection;
  onChange?: (value: ProviderSelection) => void;
}

export function ProviderSelector({ value, onChange }: ProviderSelectorProps) {
  const [internalValue, setInternalValue] = useState<ProviderSelection>({
    provider: "deepseek",
    model: "deepseek-v4-pro"
  });

  const selection = value ?? internalValue;
  const providerModels = useMemo(
    () => MODEL_CATALOG.filter((model) => model.provider === selection.provider),
    [selection.provider]
  );
  const activeModel =
    MODEL_CATALOG.find(
      (model) => model.provider === selection.provider && model.model === selection.model
    ) ?? MODEL_CATALOG[0];

  function commit(nextSelection: ProviderSelection) {
    if (value === undefined) {
      setInternalValue(nextSelection);
    }
    onChange?.(nextSelection);
  }

  function handleProviderChange(provider: ProviderName) {
    const firstAvailable =
      MODEL_CATALOG.find((model) => model.provider === provider && model.status === "available") ??
      MODEL_CATALOG.find((model) => model.provider === provider) ??
      MODEL_CATALOG[0];
    commit({ provider: firstAvailable.provider, model: firstAvailable.model });
  }

  return (
    <section className="panel-card model-provider-panel" aria-label="Model provider">
      <div className="panel-heading">
        <div>
          <p className="panel-kicker">Model Provider</p>
          <h2>Model Center</h2>
        </div>
        <Bot className="h-5 w-5 text-primary" aria-hidden="true" />
      </div>

      <label className="field-label" htmlFor="provider-select">
        Provider
      </label>
      <select
        className="field-input"
        id="provider-select"
        onChange={(event) => handleProviderChange(event.target.value as ProviderName)}
        value={selection.provider}
      >
        {PROVIDERS.map((provider) => (
          <option key={provider.provider} value={provider.provider}>
            {provider.label}
          </option>
        ))}
      </select>

      <label className="field-label" htmlFor="model-select">
        Model
      </label>
      <select
        className="field-input"
        id="model-select"
        onChange={(event) => commit({ provider: selection.provider, model: event.target.value })}
        value={selection.model}
      >
        {providerModels.map((model) => (
          <option disabled={model.status !== "available"} key={model.id} value={model.model}>
            {model.name}
            {model.status !== "available" ? " (coming soon)" : ""}
          </option>
        ))}
      </select>

      <div className="provider-model-list">
        {providerModels.map((model) => {
          const isSelected = model.model === activeModel.model && model.provider === activeModel.provider;
          const isDisabled = model.status !== "available";

          return (
            <button
              className={`provider-model-row ${isSelected ? "selected" : ""}`}
              disabled={isDisabled}
              key={model.id}
              onClick={() => commit({ provider: model.provider, model: model.model })}
              type="button"
            >
              <span className="provider-model-icon">
                <Cpu className="h-4 w-4" aria-hidden="true" />
              </span>
              <span className="provider-model-copy">
                <span className="provider-model-title">
                  {model.name}
                  {isSelected ? <Check className="h-3.5 w-3.5 text-primary" aria-hidden="true" /> : null}
                </span>
                <span>{model.description}</span>
              </span>
              {isDisabled ? <Lock className="h-3.5 w-3.5 text-muted" aria-hidden="true" /> : null}
            </button>
          );
        })}
      </div>
    </section>
  );
}
