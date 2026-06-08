"use client";

/* eslint-disable @next/next/no-img-element */

import { Boxes, Check, ChevronDown, Globe2, Landmark, Lock } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import type { ProviderName } from "@/lib/api";

export type Language = "en";
type ProviderRegion = "domestic" | "global";

type ProviderOption = {
  description: string;
  label: string;
  logoSrc: string;
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
    logoSrc: "/provider-logos/domestic/deepseek_logo.jpg",
    logoText: "DS",
    provider: "deepseek",
    region: "domestic",
    status: "available"
  },
  {
    description: "OpenAI models for advanced agentic coding workflows.",
    label: "OpenAI",
    logoSrc: "/provider-logos/overseas/open-ai_logo.jpg",
    logoText: "AI",
    provider: "openai",
    region: "global",
    status: "available"
  },
  {
    description: "Planned long-context Chinese engineering provider.",
    label: "Zhipu GLM",
    logoSrc: "/provider-logos/domestic/zhipu-glm_logo.png",
    logoText: "GLM",
    provider: "zhipu",
    region: "domestic",
    status: "coming-soon"
  },
  {
    description: "Planned coding provider for generation and refactoring.",
    label: "Qwen",
    logoSrc: "/provider-logos/domestic/qwen_logo.jpg",
    logoText: "QW",
    provider: "qwen",
    region: "domestic",
    status: "coming-soon"
  },
  {
    description: "Planned provider for review and architecture analysis.",
    label: "Anthropic Claude",
    logoSrc: "/provider-logos/overseas/claude_logo.jpg",
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
      <img alt="" onError={(event) => event.currentTarget.remove()} src={provider.logoSrc} />
      <span>{provider.logoText}</span>
    </span>
  );
}

export function ProviderSelector({ value, onChange }: ProviderSelectorProps) {
  const [region, setRegion] = useState<ProviderRegion>("domestic");
  const [isModelMenuOpen, setIsModelMenuOpen] = useState(false);
  const [internalValue, setInternalValue] = useState<ProviderSelection>({
    provider: "deepseek",
    model: "deepseek-v4-pro"
  });
  const modelMenuRef = useRef<HTMLDivElement | null>(null);

  const selection = value ?? internalValue;
  const visibleProviders = PROVIDERS.filter((provider) => provider.region === region);
  const selectedProvider = PROVIDERS.find((provider) => provider.provider === selection.provider) ?? PROVIDERS[0];
  const providerModels = useMemo(
    () => MODELS.filter((model) => model.provider === selection.provider),
    [selection.provider]
  );
  const selectedModel = providerModels.find((model) => model.model === selection.model) ?? providerModels[0];

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
    setIsModelMenuOpen(false);
  }

  return (
    <section className="panel-card model-provider-panel" aria-label="Model provider">
      <div className="panel-heading">
        <div>
          <h2>Model Center</h2>
          <p className="panel-description">Choose the provider and active coding model.</p>
        </div>
        <Boxes className="h-5 w-5 text-primary" aria-hidden="true" />
      </div>

      <p className="field-label">Model Provider</p>
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

      <label className="field-label" id="model-select-label">
        Current Model
      </label>
      <div
        className="model-select"
        onBlur={(event) => {
          if (!modelMenuRef.current?.contains(event.relatedTarget as Node | null)) {
            setIsModelMenuOpen(false);
          }
        }}
        ref={modelMenuRef}
      >
        <button
          aria-expanded={isModelMenuOpen}
          aria-haspopup="listbox"
          aria-labelledby="model-select-label"
          className="model-select-trigger"
          onClick={() => setIsModelMenuOpen((open) => !open)}
          type="button"
        >
          <span>{selectedModel?.name ?? "Select model"}</span>
          <ChevronDown className={`h-4 w-4 ${isModelMenuOpen ? "rotate-180" : ""}`} aria-hidden="true" />
        </button>
        {isModelMenuOpen ? (
          <div className="model-select-menu" role="listbox" aria-labelledby="model-select-label">
            {providerModels.map((model) => {
              const isSelected = model.model === selection.model;
              const isDisabled = model.status !== "available";
              return (
                <button
                  aria-selected={isSelected}
                  className={`model-select-option ${isSelected ? "selected" : ""}`}
                  disabled={isDisabled}
                  key={model.id}
                  onClick={() => {
                    if (isDisabled) return;
                    commit({ provider: selection.provider, model: model.model });
                    setIsModelMenuOpen(false);
                  }}
                  role="option"
                  type="button"
                >
                  <span>
                    <strong>{model.name}</strong>
                    <small>{model.description}</small>
                  </span>
                  {isSelected ? <Check className="h-3.5 w-3.5" aria-hidden="true" /> : null}
                  {isDisabled ? <Lock className="h-3.5 w-3.5" aria-hidden="true" /> : null}
                </button>
              );
            })}
          </div>
        ) : null}
      </div>
    </section>
  );
}
