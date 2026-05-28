"use client";

import { Check, Settings2 } from "lucide-react";
import { useMemo, useState } from "react";
import type { ProviderName } from "@/lib/api";

type ProviderOption = {
  label: string;
  value: ProviderName;
  defaultModel: string;
  models: string[];
};

const PROVIDERS: ProviderOption[] = [
  {
    label: "OpenAI",
    value: "openai",
    defaultModel: "gpt-5.2",
    models: ["gpt-5.2", "gpt-4o-mini"]
  },
  {
    label: "DeepSeek",
    value: "deepseek",
    defaultModel: "deepseek-v4-pro",
    models: ["deepseek-v4-pro", "deepseek-chat"]
  }
];

export interface ProviderSelection {
  provider: ProviderName;
  model: string;
}

export interface ProviderSelectorProps {
  value?: ProviderSelection;
  onChange?: (value: ProviderSelection) => void;
}

export function ProviderSelector({ value, onChange }: ProviderSelectorProps) {
  const [internalValue, setInternalValue] = useState<ProviderSelection>({
    provider: PROVIDERS[0].value,
    model: PROVIDERS[0].defaultModel
  });

  const selection = value ?? internalValue;
  const activeProvider =
    PROVIDERS.find((provider) => provider.value === selection.provider) ?? PROVIDERS[0];

  const model = activeProvider.models.includes(selection.model)
    ? selection.model
    : activeProvider.defaultModel;

  const summary = useMemo(() => `${activeProvider.label} / ${model}`, [activeProvider.label, model]);

  function update(nextSelection: ProviderSelection) {
    if (value === undefined) {
      setInternalValue(nextSelection);
    }
    onChange?.(nextSelection);
  }

  function selectProvider(provider: ProviderOption) {
    update({
      provider: provider.value,
      model: provider.defaultModel
    });
  }

  function selectModel(nextModel: string) {
    update({
      provider: activeProvider.value,
      model: nextModel
    });
  }

  return (
    <section className="rounded-lg border border-border bg-panel p-4 shadow-soft">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Settings2 className="h-4 w-4 text-primary" aria-hidden="true" />
          Model
        </div>
        <span className="max-w-[150px] truncate rounded-md bg-background px-2 py-1 text-xs text-muted">
          {summary}
        </span>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2" role="group" aria-label="Provider">
        {PROVIDERS.map((provider) => {
          const isActive = provider.value === activeProvider.value;
          return (
            <button
              className={`flex h-10 items-center justify-center gap-2 rounded-md border px-3 text-sm font-medium transition ${
                isActive
                  ? "border-primary bg-[#edf4ff] text-primary"
                  : "border-border bg-white text-foreground hover:border-primary"
              }`}
              key={provider.value}
              onClick={() => selectProvider(provider)}
              type="button"
            >
              {isActive ? <Check className="h-4 w-4" aria-hidden="true" /> : null}
              {provider.label}
            </button>
          );
        })}
      </div>

      <label className="mb-2 block text-xs font-medium uppercase text-muted" htmlFor="model">
        Model
      </label>
      <select
        className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm"
        id="model"
        onChange={(event) => selectModel(event.target.value)}
        value={model}
      >
        {activeProvider.models.map((modelOption) => (
          <option key={modelOption} value={modelOption}>
            {modelOption}
          </option>
        ))}
      </select>
    </section>
  );
}
