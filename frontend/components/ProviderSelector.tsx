"use client";

/* eslint-disable @next/next/no-img-element */

import { Boxes, Check, ChevronDown, Globe2, Landmark, Loader2, Lock, RefreshCw } from "lucide-react";
import { useRef, useState } from "react";
import type { ProviderName } from "@/lib/api";
import { useProviderConfig } from "@/hooks/useProviderConfig";

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

const PROVIDERS: ProviderOption[] = [
  { description: "Strong coding and repository reasoning provider.", label: "DeepSeek", logoSrc: "/provider-logos/domestic/deepseek_logo.jpg", logoText: "DS", provider: "deepseek", region: "domestic", status: "available" },
  { description: "OpenAI models for advanced agentic coding workflows.", label: "OpenAI", logoSrc: "/provider-logos/overseas/open-ai_logo.jpg", logoText: "AI", provider: "openai", region: "global", status: "available" },
  { description: "Planned long-context Chinese engineering provider.", label: "Zhipu GLM", logoSrc: "/provider-logos/domestic/zhipu-glm_logo.png", logoText: "GLM", provider: "zhipu", region: "domestic", status: "coming-soon" },
  { description: "Planned coding provider for generation and refactoring.", label: "Qwen", logoSrc: "/provider-logos/domestic/qwen_logo.jpg", logoText: "QW", provider: "qwen", region: "domestic", status: "coming-soon" },
  { description: "Planned provider for review and architecture analysis.", label: "Anthropic Claude", logoSrc: "/provider-logos/overseas/claude_logo.jpg", logoText: "CL", provider: "claude", region: "global", status: "coming-soon" },
];

// Curated fallback models shown before key is entered / fetched.
const FALLBACK_MODELS: Partial<Record<ProviderName, string[]>> = {
  deepseek: ["deepseek-chat", "deepseek-reasoner"],
  openai: ["gpt-4o", "gpt-4o-mini", "o3-mini"],
};

export interface ProviderSelection {
  provider: ProviderName;
  model: string;
  apiKey?: string;
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
  const [draftKey, setDraftKey] = useState("");
  // Start with no selection — user picks provider + model explicitly
  const [internalValue, setInternalValue] = useState<ProviderSelection>({ provider: "deepseek", model: "" });
  const modelMenuRef = useRef<HTMLDivElement | null>(null);

  const { getKey, setKey, models, isLoadingModels, modelsError, fetchModels } = useProviderConfig();

  const selection = value ?? internalValue;
  const visibleProviders = PROVIDERS.filter((p) => p.region === region);
  const selectedProvider = PROVIDERS.find((p) => p.provider === selection.provider) ?? PROVIDERS[0];
  const providerModels = models[selection.provider] ?? FALLBACK_MODELS[selection.provider] ?? [];
  const savedKey = getKey(selection.provider);

  function commit(next: ProviderSelection) {
    if (value === undefined) setInternalValue(next);
    onChange?.(next);
  }

  function selectProvider(provider: ProviderOption) {
    if (provider.status !== "available") return;
    const saved = getKey(provider.provider);
    const currentModels = models[provider.provider] ?? FALLBACK_MODELS[provider.provider] ?? [];
    const firstModel = currentModels[0] ?? "";
    commit({ provider: provider.provider, model: firstModel, apiKey: saved || undefined });
    setIsModelMenuOpen(false);
    setDraftKey("");
  }

  async function handleFetchModels() {
    const fetched = await fetchModels(selection.provider);
    if (fetched.length > 0) {
      commit({ ...selection, model: fetched[0] });
    }
  }

  function handleSaveKey() {
    const trimmed = draftKey.trim();
    if (!trimmed) return;
    setKey(selection.provider, trimmed);
    commit({ ...selection, apiKey: trimmed });
    setDraftKey("");
  }

  return (
    <section className="panel-card model-provider-panel" aria-label="Model provider">
      <div className="panel-heading">
        <div>
          <h2>Model Center</h2>
          <p className="panel-description">Choose provider, enter API key, then load models.</p>
        </div>
        <Boxes className="h-5 w-5 text-primary" aria-hidden="true" />
      </div>

      {/* Region tabs */}
      <p className="field-label">Model Provider</p>
      <div className="segmented-control model-region-tabs" role="tablist" aria-label="Model source">
        <button className={region === "domestic" ? "active" : ""} onClick={() => setRegion("domestic")} type="button">
          <Landmark className="h-3.5 w-3.5" aria-hidden="true" /> Domestic
        </button>
        <button className={region === "global" ? "active" : ""} onClick={() => setRegion("global")} type="button">
          <Globe2 className="h-3.5 w-3.5" aria-hidden="true" /> Global
        </button>
      </div>

      {/* Provider list */}
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
              {isSelected && <Check className="h-3.5 w-3.5 text-primary" aria-hidden="true" />}
              {isDisabled && <Lock className="h-3.5 w-3.5 text-muted" aria-hidden="true" />}
            </button>
          );
        })}
      </div>

      {/* API Key — single row: input + Save button */}
      <label className="field-label" htmlFor="provider-api-key">API Key</label>
      <div style={{ display: "flex", gap: "8px", marginBottom: "4px" }}>
        <input
          className="field-input"
          id="provider-api-key"
          onChange={(e) => setDraftKey(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleSaveKey(); }}
          placeholder={savedKey ? "Key saved — enter new to replace" : `${selectedProvider.label} API key…`}
          style={{ flex: 1 }}
          type="password"
          value={draftKey}
        />
        <button
          className="secondary-button"
          disabled={!draftKey.trim()}
          onClick={handleSaveKey}
          style={{ flexShrink: 0 }}
          type="button"
        >
          Save
        </button>
      </div>
      {savedKey && <p className="workspace-hint" style={{ marginBottom: "8px" }}>✓ Key saved for {selectedProvider.label}</p>}

      {/* Model select — label + reload button in one flex row */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
        <label className="field-label" id="model-select-label" style={{ margin: 0 }}>
          Current Model
        </label>
        <button
          aria-label="Reload models from provider"
          className="icon-button compact app-tooltip"
          data-tooltip={savedKey ? "Load models for this key" : "Save a key first"}
          disabled={isLoadingModels || !savedKey}
          onClick={handleFetchModels}
          type="button"
        >
          {isLoadingModels ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
        </button>
      </div>
      {modelsError && <p className="error-box" style={{ marginBottom: "8px", fontSize: "12px" }}>{modelsError}</p>}

      <div
        className="model-select"
        onBlur={(e) => { if (!modelMenuRef.current?.contains(e.relatedTarget as Node | null)) setIsModelMenuOpen(false); }}
        ref={modelMenuRef}
      >
        <button
          aria-expanded={isModelMenuOpen}
          aria-haspopup="listbox"
          aria-labelledby="model-select-label"
          className="model-select-trigger"
          onClick={() => setIsModelMenuOpen((o) => !o)}
          type="button"
        >
          <span>{selection.model || "Select model"}</span>
          <ChevronDown className={`h-4 w-4 ${isModelMenuOpen ? "rotate-180" : ""}`} aria-hidden="true" />
        </button>
        {isModelMenuOpen && providerModels.length > 0 && (
          <div className="model-select-menu" role="listbox" aria-labelledby="model-select-label">
            {providerModels.map((modelId) => {
              const isSelected = modelId === selection.model;
              return (
                <button
                  aria-selected={isSelected}
                  className={`model-select-option ${isSelected ? "selected" : ""}`}
                  key={modelId}
                  onClick={() => { commit({ ...selection, model: modelId }); setIsModelMenuOpen(false); }}
                  role="option"
                  type="button"
                >
                  <span><strong>{modelId}</strong></span>
                  {isSelected && <Check className="h-3.5 w-3.5" aria-hidden="true" />}
                </button>
              );
            })}
          </div>
        )}
        {isModelMenuOpen && providerModels.length === 0 && (
          <div className="model-select-menu">
            <p style={{ padding: "10px 12px", margin: 0, color: "var(--muted)", fontSize: "13px" }}>
              {savedKey ? "Click ↺ above to load models" : "Save an API key, then click ↺"}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
