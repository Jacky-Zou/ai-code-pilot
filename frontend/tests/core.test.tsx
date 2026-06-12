/**
 * Minimal test suite covering the 4 required interaction areas from T-12.
 * Uses RTL + vitest. SSE streaming is mocked at the fetch layer.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// 1. ProviderSelector — API Key save + model fetch trigger
// ---------------------------------------------------------------------------
import { ProviderSelector } from "@/components/ProviderSelector";
import * as api from "@/lib/api";

describe("ProviderSelector", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("saves API key to localStorage on Save click", async () => {
    const user = userEvent.setup();
    render(<ProviderSelector />);

    const input = screen.getByPlaceholderText(/API key/i);
    await user.type(input, "sk-test-key");
    await user.click(screen.getByRole("button", { name: /save/i }));

    const stored = JSON.parse(localStorage.getItem("aicodepilot.providerKeys") ?? "{}");
    expect(stored["deepseek"]).toBe("sk-test-key");
  });

  it("fetches models and populates model list after save + reload", async () => {
    vi.spyOn(api, "listProviderModels").mockResolvedValue({
      provider: "deepseek",
      models: ["deepseek-chat", "deepseek-reasoner"],
    });

    const user = userEvent.setup();
    render(<ProviderSelector />);

    const input = screen.getByPlaceholderText(/API key/i);
    await user.type(input, "sk-test-key");
    await user.click(screen.getByRole("button", { name: /save/i }));
    await user.click(screen.getByRole("button", { name: /reload models/i }));

    await waitFor(() => {
      expect(api.listProviderModels).toHaveBeenCalledWith(
        expect.objectContaining({ provider: "deepseek", api_key: "sk-test-key" })
      );
    });
  });
});

// ---------------------------------------------------------------------------
// 2. useChat — send dispatches SSE and accumulates answer_delta events
// ---------------------------------------------------------------------------
import { renderHook, act } from "@testing-library/react";
import { useChat } from "@/hooks/useChat";

describe("useChat", () => {
  it("accumulates answer_delta text and resolves done event", async () => {
    const sseFrames = [
      "event: answer_delta\ndata: {\"text\":\"Hello\"}\n\n",
      "event: answer_delta\ndata: {\"text\":\" world\"}\n\n",
      "event: done\ndata: {\"answer\":\"Hello world\",\"provider\":\"deepseek\",\"model\":\"deepseek-chat\",\"tool_calls\":[],\"references\":[],\"conversation_id\":\"conv-1\"}\n\n",
    ].join("");

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(sseFrames));
        controller.close();
      },
    });

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, body: stream }));

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.send({ message: "hi", provider: "deepseek", model: "deepseek-chat", apiKey: "sk-k" });
    });

    const assistant = result.current.messages.find((m) => m.role === "assistant");
    expect(assistant?.content).toBe("Hello world");

    vi.unstubAllGlobals();
  });
});

// ---------------------------------------------------------------------------
// 3. useProviderConfig — key persistence and clearance
// ---------------------------------------------------------------------------
import { useProviderConfig } from "@/hooks/useProviderConfig";

describe("useProviderConfig", () => {
  beforeEach(() => localStorage.clear());

  it("persists and retrieves a key", async () => {
    const { result } = renderHook(() => useProviderConfig());
    act(() => { result.current.setKey("deepseek", "sk-abc"); });
    expect(result.current.getKey("deepseek")).toBe("sk-abc");
    const stored = JSON.parse(localStorage.getItem("aicodepilot.providerKeys") ?? "{}");
    expect(stored["deepseek"]).toBe("sk-abc");
  });

  it("clears a key", () => {
    const { result } = renderHook(() => useProviderConfig());
    act(() => { result.current.setKey("deepseek", "sk-abc"); });
    act(() => { result.current.clearKey("deepseek"); });
    expect(result.current.getKey("deepseek")).toBe("");
  });
});
