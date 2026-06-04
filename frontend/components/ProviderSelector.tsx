"use client";

import { Boxes, Check, Cpu, Globe2, Landmark, Lock } from "lucide-react";
import { useMemo, useState } from "react";
import type { ProviderName } from "@/lib/api";

export type Language = "en";
type ProviderRegion = "domestic" | "global";

type ProviderOption = {
  description: string;
  label: string;
  logoText: string;
  provider: ProviderName;
  region: ProviderRegion;
  status: "available" | "coming-soon";
};

type ModelOption = {
  description: string;
  id: string;
  model: string;
  name: string;
  provider: ProviderName;
  status: "available" | "coming-soon";
};

const PROVIDERS: ProviderOption[] = [
  {
    description: "Strong coding and repository reasoning provider.",
    label: "DeepSeek",
    logoText: "DS",
    provider: "deepseek",
    region: "domestic",
    status: "available"
  },
  {
    description: "OpenAI models for advanced agentic coding workflows.",
    label: "OpenAI",
    logoText: "AI",
    provider: "openai",
    region: "global",
    status: "available"
  },
  {
    description: "Planned long-context Chinese engineering provider.",
    label: "Zhipu GLM",
    logoText: "GLM",
    provider: "zhipu",
    region: "domestic",
    status: "coming-soon"
  },
  {
    description: "Planned coding provider for generation and refactoring.",
    label: "Qwen",
    logoText: "QW",
    provider: "qwen",
    region: "domestic",
    status: "coming-soon"
  },
  {
    description: "Planned provider for review and architecture analysis.",
    label: "Anthropic Claude",
    logoText: "CL",
    provider: "claude",
    region: "global",
    status: "coming-soon"
  }
];

const MODELS: ModelOption[] = [
  {
    description: "Default coding model for repository analysis and tool calling.",
    id: "deepseek-v4-pro",
    model: "deepseek-v4-pro",
    name: "DeepSeek V4-Pro",
    provider: "deepseek",
    status: "available"
  },
  {
    description: "OpenAI coding model option for agentic workflows.",
    id: "gpt-5-2",
    model: "gpt-5.2",
    name: "GPT-5.2",
    provider: "openai",
    status: "available"
  },
  {
    description: "Planned GLM long-context model.",
    id: "glm-4-6",
    model: "glm-4.6",
    name: "GLM-4.6",
    provider: "zhipu",
    status: "coming-soon"
  },
  {
    description: "Planned Qwen coding model.",
    id: "qwen-coder-latest",
    model: "qwen-coder-latest",
    name: "Qwen Coder",
    provider: "qwen",
    status: "coming-soon"
  },
  {
    description: "Planned Claude model for deep code review.",
    id: "claude-sonnet-latest",
    model: "claude-sonnet-latest",
    name: "Claude Sonnet",
    provider: "claude",
    status: "coming-soon"
  }
];

export interface ProviderSelection {
  provider: ProviderName;
  model: string;
}

export interface ProviderSelectorProps {
  language?: Language;
  value?: ProviderSelection;
  onChange?: (value: ProviderSelection) => void;
}

function ProviderLogo({ provider }: { provider: ProviderOption }) {
  return (
    <span className={`provider-logo provider-logo-${provider.provider}`} aria-hidden="true">
      {provider.logoText}
    </span>
  );
}

export function ProviderSelector({ value, onChange }: ProviderSelectorProps) {
  const [region, setRegion] = useState<ProviderRegion>("domestic");
  const [internalValue, setInternalValue] = useState<ProviderSelection>({
    provider: "deepseek",
    model: "deepseek-v4-pro"
  });

  const selection = value ?? internalValue;
  const visibleProviders = PROVIDERS.filter((provider) => provider.region === region);
  const selectedProvider = PROVIDERS.find((provider) => provider.provider === selection.provider) ?? PROVIDERS[0];
  const providerModels = useMemo(
    () => MODELS.filter((model) => model.provider === selection.provider),
    [selection.provider]
  );
  const selectedModel =
    MODELS.find((model) => model.provider === selection.provider && model.model === selection.model) ?? providerModels[0];

  function commit(nextSelection: ProviderSelection) {
    if (value === undefined) {
      setInternalValue(nextSelection);
    }
    onChange?.(nextSelection);
  }

  function selectProvider(provider: ProviderOption) {
    if (provider.status !== "available") return;
    const firstModel = MODELS.find((model) => model.provider === provider.provider && model.status === "available");
    if (!firstModel) return;
    commit({ provider: provider.provider, model: firstModel.model });
  }

  return (
    <section className="panel-card model-provider-panel" aria-label="Model provider">
      <div className="panel-heading">
        <div>
          <p className="panel-kicker">Model Provider</p>
          <h2>Model Center</h2>
        </div>
        <Boxes className="h-5 w-5 text-primary" aria-hidden="true" />
      </div>

      <div className="segmented-control model-region-tabs" role="tablist" aria-label="Model source">
        <button className={region === "domestic" ? "active" : ""} onClick={() => setRegion("domestic")} type="button">
          <Landmark className="h-3.5 w-3.5" aria-hidden="true" />
          Domestic
        </button>
        <button className={region === "global" ? "active" : ""} onClick={() => setRegion("global")} type="button">
          <Globe2 className="h-3.5 w-3.5" aria-hidden="true" />
          Global
        </button>
      </div>

      <div className="provider-list" aria-label="Provider list">
        {visibleProviders.map((provider) => {
          const isSelected = selectedProvider.provider === provider.provider;
          const isDisabled = provider.status !== "available";

          return (
            <button
              className={`provider-option ${isSelected ? "selected" : ""}`}
              disabled={isDisabled}
              key={provider.provider}
              onClick={() => selectProvider(provider)}
              type="button"
            >
              <ProviderLogo provider={provider} />
              <span>
                <strong>{provider.label}</strong>
                <small>{provider.description}</small>
              </span>
              {isSelected ? <Check className="h-3.5 w-3.5 text-primary" aria-hidden="true" /> : null}
              {isDisabled ? <Lock className="h-3.5 w-3.5 text-muted" aria-hidden="true" /> : null}
            </button>
          );
        })}
      </div>

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

      {selectedModel ? (
        <div className="provider-model-row selected">
          <span className="provider-model-icon">
            <Cpu className="h-4 w-4" aria-hidden="true" />
          </span>
          <span className="provider-model-copy">
            <span className="provider-model-title">
              {selectedModel.name}
              <Check className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
            </span>
            <span>{selectedModel.description}</span>
          </span>
        </div>
      ) : null}
    </section>
  );
}
