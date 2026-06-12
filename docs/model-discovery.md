# Model Discovery

`POST /api/providers/models` returns the model ids a provider API key can actually use.

## Request

```json
{
  "provider": "deepseek",
  "api_key": "sk-...",
  "base_url": null
}
```

`base_url` is optional — omit it to use the provider's default endpoint from server settings.

## Response

```json
{
  "provider": "deepseek",
  "models": ["deepseek-chat", "deepseek-reasoner"]
}
```

## How it works

The backend proxies a `GET {base_url}/models` call (OpenAI-compatible catalog endpoint) using the
supplied key. The key is used only for this one catalog call and the subsequent chat requests —
it is never logged or persisted server-side. The frontend stores the key in `localStorage` under
the key `aicodepilot.providerKeys`.

## Frontend flow

1. User selects a provider in the **Model Center** panel
2. User types their API key and clicks **Save** — key persisted to `localStorage`
3. User clicks **↺ (Reload models)** — frontend calls `POST /api/providers/models`
4. Model dropdown is populated with the real, key-specific model list
5. Every subsequent chat request includes `api_key` + `provider` in the request body

## Supported providers

| Provider | Default base URL |
|---|---|
| `openai` | `https://api.openai.com/v1` |
| `deepseek` | `https://api.deepseek.com` |
