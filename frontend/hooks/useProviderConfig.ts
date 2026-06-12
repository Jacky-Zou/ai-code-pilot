"use client";

import { useCallback, useEffect, useState } from "react";
import { listProviderModels, type ProviderName } from "@/lib/api";

/**
 * Manages bring-your-own-key provider credentials and dynamic model discovery.
 *
 * API keys are stored in the browser (localStorage) — never sent anywhere except
 * to our backend, which forwards them only to authenticate the provider's
 * `/v1/models` catalog call and chat completions. This mirrors how Cline /
 * Continue / Aider handle keys: the key decides which models are available, so
 * after the user saves a key we fetch the real, key-specific model list rather
 * than guessing from a hardcoded table.
 */

const STORAGE_KEY = "aicodepilot.providerKeys";

export type ProviderKeys = Partial<Record<ProviderName, string>>;

function loadKeys(): ProviderKeys {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as ProviderKeys) : {};
  } catch {
    return {};
  }
}

function persistKeys(keys: ProviderKeys): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
}

export function useProviderConfig() {
  const [keys, setKeys] = useState<ProviderKeys>({});
  const [models, setModels] = useState<Record<string, string[]>>({});
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);

  // Restore persisted keys on mount (client-only to avoid SSR mismatch).
  useEffect(() => {
    setKeys(loadKeys());
  }, []);

  const getKey = useCallback(
    (provider: ProviderName): string => keys[provider] ?? "",
    [keys]
  );

  const setKey = useCallback((provider: ProviderName, value: string) => {
    setKeys((prev) => {
      const next = { ...prev, [provider]: value };
      persistKeys(next);
      return next;
    });
  }, []);

  const clearKey = useCallback((provider: ProviderName) => {
    setKeys((prev) => {
      const next = { ...prev };
      delete next[provider];
      persistKeys(next);
      return next;
    });
    setModels((prev) => {
      const next = { ...prev };
      delete next[provider];
      return next;
    });
  }, []);

  // Fetch the model list a saved key can actually use via the backend proxy.
  const fetchModels = useCallback(
    async (provider: ProviderName): Promise<string[]> => {
      const apiKey = keys[provider];
      if (!apiKey) {
        setModelsError("Enter and save an API key first.");
        return [];
      }
      setIsLoadingModels(true);
      setModelsError(null);
      try {
        const response = await listProviderModels({ provider, api_key: apiKey });
        setModels((prev) => ({ ...prev, [provider]: response.models }));
        return response.models;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to load models";
        setModelsError(msg);
        return [];
      } finally {
        setIsLoadingModels(false);
      }
    },
    [keys]
  );

  return {
    getKey,
    setKey,
    clearKey,
    models,
    isLoadingModels,
    modelsError,
    fetchModels,
  };
}
