# SSE Streaming Protocol

`POST /api/chat/stream` streams agent execution as Server-Sent Events.

## Event Types

| Event | Data fields | When emitted |
|---|---|---|
| `thinking` | `step: int` | Before each LLM call |
| `tool_start` | `tool: str, arguments: {...}` | Before tool execution |
| `tool_end` | `tool: str, error: str\|null` | After tool execution |
| `answer_delta` | `text: str` | Reserved for token-level streaming |
| `done` | `answer, provider, model, tool_calls, references, patch_suggestions, conversation_id` | Final event |
| `error` | `detail: str` | On unrecoverable exception |

## Wire Format

Each event is a standard SSE frame:

```
event: thinking
data: {"step": 1}

event: tool_start
data: {"tool": "read_file", "arguments": {"file_path": "app/main.py"}}

event: tool_end
data: {"tool": "read_file", "error": null}

event: done
data: {"answer": "...", "conversation_id": "abc-123", ...}
```

## Client Request

```json
POST /api/chat/stream
Content-Type: application/json

{
  "message": "How is the agent loop implemented?",
  "project_path": "/workspace/AICodePilot",
  "conversation_id": "abc-123"
}
```

Include `conversation_id` from a prior `done` event to continue a multi-turn session.

## Frontend Integration

The frontend uses `lib/sse.ts:consumeSse()` which opens a POST request and reads the `ReadableStream` manually (native `EventSource` only supports GET). See `hooks/useChat.ts` for the full dispatch logic.
