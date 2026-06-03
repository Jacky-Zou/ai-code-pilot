"use client";

/* eslint-disable @next/next/no-img-element */

import { Check, Globe2, Landmark, Lock, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import type { ProviderName } from "@/lib/api";

export type Language = "zh" | "en";

type ModelRegion = "cn" | "global";

type ModelOption = {
  id: string;
  name: string;
  providerLabel: string;
  provider: ProviderName;
  model: string;
  region: ModelRegion;
  description: Record<Language, string>;
  logoUrl?: string;
  logoText: string;
  status: "available" | "default" | "coming-soon";
};

const MODEL_CATALOG: ModelOption[] = [
  {
    id: "deepseek-v4-pro",
    name: "DeepSeek V4-Pro",
    providerLabel: "DeepSeek",
    provider: "deepseek",
    model: "deepseek-v4-pro",
    region: "cn",
    description: {
      zh: "默认模型，适合代码库理解、推理和工具调用。",
      en: "Default model for codebase reasoning and tool calling."
    },
    logoUrl: undefined,
    logoText: "DS",
    status: "default"
  },
  {
    id: "deepseek-v4-flash",
    name: "DeepSeek V4-Flash",
    providerLabel: "DeepSeek",
    provider: "deepseek",
    model: "deepseek-v4-flash",
    region: "cn",
    description: {
      zh: "低延迟版本，适合快速问答和代码定位。",
      en: "Low-latency option for fast code Q&A."
    },
    logoUrl: undefined,
    logoText: "DS",
    status: "coming-soon"
  },
  {
    id: "glm-4-6",
    name: "GLM-4.6",
    providerLabel: "Zhipu GLM",
    provider: "zhipu",
    model: "glm-4.6",
    region: "cn",
    description: {
      zh: "预留长上下文与中文 Agent 工作流接入。",
      en: "Reserved for long-context Chinese Agent workflows."
    },
    logoUrl: undefined,
    logoText: "GLM",
    status: "coming-soon"
  },
  {
    id: "qwen3-6-plus",
    name: "Qwen3.6 Plus",
    providerLabel: "Qwen",
    provider: "qwen",
    model: "qwen3.6-plus",
    region: "cn",
    description: {
      zh: "预留中文工程分析、说明生成和通用问答能力。",
      en: "Reserved for Chinese engineering analysis."
    },
    logoUrl: undefined,
    logoText: "QW",
    status: "coming-soon"
  },
  {
    id: "qwen3-coder-plus",
    name: "Qwen3 Coder Plus",
    providerLabel: "Qwen Coder",
    provider: "qwen",
    model: "qwen3-coder-plus",
    region: "cn",
    description: {
      zh: "预留代码生成、重构和多文件修改能力。",
      en: "Reserved for generation and refactoring."
    },
    logoUrl: undefined,
    logoText: "QW",
    status: "coming-soon"
  },
  {
    id: "gpt-5-2",
    name: "GPT-5.2",
    providerLabel: "OpenAI",
    provider: "openai",
    model: "gpt-5.2",
    region: "global",
    description: {
      zh: "预留旗舰代码与 Agent 任务模型。",
      en: "Reserved flagship model for coding and agentic tasks."
    },
    logoUrl: undefined,
    logoText: "AI",
    status: "available"
  },
  {
    id: "gpt-4o",
    name: "GPT-4o",
    providerLabel: "OpenAI",
    provider: "openai",
    model: "gpt-4o",
    region: "global",
    description: {
      zh: "预留多模态与快速工程问答能力。",
      en: "Reserved multimodal and fast engineering Q&A option."
    },
    logoUrl: undefined,
    logoText: "AI",
    status: "coming-soon"
  },
  {
    id: "claude-opus",
    name: "Claude Opus",
    providerLabel: "Anthropic",
    provider: "claude",
    model: "claude-opus-latest",
    region: "global",
    description: {
      zh: "预留深度代码审查和架构分析能力。",
      en: "Reserved for deep review and architecture analysis."
    },
    logoUrl: undefined,
    logoText: "CL",
    status: "coming-soon"
  },
  {
    id: "claude-sonnet",
    name: "Claude Sonnet",
    providerLabel: "Anthropic",
    provider: "claude",
    model: "claude-sonnet-latest",
    region: "global",
    description: {
      zh: "预留速度与质量平衡的代码助手能力。",
      en: "Reserved for balanced code assistance."
    },
    logoUrl: undefined,
    logoText: "CL",
    status: "coming-soon"
  }
];

const LABELS = {
  zh: {
    title: "模型中心",
    domestic: "国内模型",
    global: "国外模型",
    active: "当前",
    coming: "待接入",
    available: "可用"
  },
  en: {
    title: "Model Hub",
    domestic: "Domestic",
    global: "Global",
    active: "Active",
    coming: "Coming soon",
    available: "Available"
  }
};

export interface ProviderSelection {
  provider: ProviderName;
  model: string;
}

export interface ProviderSelectorProps {
  language?: Language;
  value?: ProviderSelection;
  onChange?: (value: ProviderSelection) => void;
}

function modelStatusLabel(status: ModelOption["status"], language: Language): string {
  if (status === "coming-soon") return LABELS[language].coming;
  if (status === "default") return LABELS[language].active;
  return LABELS[language].available;
}

function ModelLogo({ model }: { model: ModelOption }) {
  const [failed, setFailed] = useState(false);

  return (
    <span className={`model-logo ${failed || !model.logoUrl ? "fallback" : ""}`} aria-hidden="true">
      {!failed && model.logoUrl ? (
        <img alt="" onError={() => setFailed(true)} src={model.logoUrl} />
      ) : (
        <span>{model.logoText}</span>
      )}
    </span>
  );
}

export function ProviderSelector({ language = "zh", value, onChange }: ProviderSelectorProps) {
  const [region, setRegion] = useState<ModelRegion>("cn");
  const [internalValue, setInternalValue] = useState<ProviderSelection>({
    provider: "deepseek",
    model: "deepseek-v4-pro"
  });

  const labels = LABELS[language];
  const selection = value ?? internalValue;
  const activeModel =
    MODEL_CATALOG.find(
      (model) => model.provider === selection.provider && model.model === selection.model
    ) ?? MODEL_CATALOG[0];
  const visibleModels = useMemo(
    () => MODEL_CATALOG.filter((model) => model.region === region),
    [region]
  );

  function update(nextSelection: ProviderSelection) {
    if (value === undefined) {
      setInternalValue(nextSelection);
    }
    onChange?.(nextSelection);
  }

  return (
    <section className="panel-card model-hub-panel">
      <div className="panel-heading">
        <div>
          <p className="panel-kicker">{activeModel.providerLabel}</p>
          <h2>{labels.title}</h2>
        </div>
        <Sparkles className="h-5 w-5 text-primary" aria-hidden="true" />
      </div>

      <div className="segmented-control" role="tablist" aria-label={labels.title}>
        <button
          className={region === "cn" ? "active" : ""}
          onClick={() => setRegion("cn")}
          type="button"
        >
          <Landmark className="h-3.5 w-3.5" aria-hidden="true" />
          {labels.domestic}
        </button>
        <button
          className={region === "global" ? "active" : ""}
          onClick={() => setRegion("global")}
          type="button"
        >
          <Globe2 className="h-3.5 w-3.5" aria-hidden="true" />
          {labels.global}
        </button>
      </div>

      <div className="model-list">
        {visibleModels.map((model) => {
          const isSelected = model.provider === selection.provider && model.model === selection.model;
          const isDisabled = model.status === "coming-soon";

          return (
            <button
              className={`model-card ${isSelected ? "selected" : ""}`}
              disabled={isDisabled}
              key={model.id}
              onClick={() => update({ provider: model.provider, model: model.model })}
              type="button"
            >
              <ModelLogo model={model} />
              <span className="min-w-0 flex-1 text-left">
                <span className="model-name-row">
                  <span className="truncate text-sm font-semibold">{model.name}</span>
                  {isSelected ? <Check className="h-3.5 w-3.5 shrink-0 text-primary" /> : null}
                </span>
                <span className="mt-1 block truncate text-xs text-muted">
                  {model.providerLabel} / {model.model}
                </span>
                <span className="model-description">{model.description[language]}</span>
              </span>
              <span className={`status-pill ${isDisabled ? "muted" : "ready"}`}>
                {isDisabled ? <Lock className="h-3 w-3" aria-hidden="true" /> : null}
                {modelStatusLabel(model.status, language)}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
