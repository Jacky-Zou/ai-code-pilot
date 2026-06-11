/**
 * SSE frame parser for POST-based event streams.
 *
 * Native EventSource only supports GET, so we use fetch + ReadableStream and
 * parse SSE frames manually. Each frame is delimited by a blank line; `event:`
 * and `data:` lines are accumulated per frame.
 */

export interface SseEvent {
  type: string;
  data: Record<string, unknown>;
}

/**
 * Consume a POST SSE stream and call onEvent for each complete frame.
 *
 * Buffers partial chunks until a complete frame (terminated by \\n\\n) is
 * available, then parses its event/data lines and dispatches the result.
 */
export async function consumeSse(
  url: string,
  body: unknown,
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Stream request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let separatorIndex: number;
    while ((separatorIndex = buffer.indexOf("\n\n")) !== -1) {
      const rawFrame = buffer.slice(0, separatorIndex);
      buffer = buffer.slice(separatorIndex + 2);
      const event = parseFrame(rawFrame);
      if (event) onEvent(event);
    }
  }
}

function parseFrame(rawFrame: string): SseEvent | null {
  let eventType = "message";
  const dataLines: string[] = [];

  for (const line of rawFrame.split("\n")) {
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  if (dataLines.length === 0) return null;

  try {
    return { type: eventType, data: JSON.parse(dataLines.join("\n")) };
  } catch {
    return null;
  }
}
