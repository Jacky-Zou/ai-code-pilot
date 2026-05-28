# Agent Design

The first implementation intentionally hand-writes the Agent loop instead of depending on LangChain, CrewAI, AutoGen, or another large Agent framework.

## Goals

- Make tool calling explicit and explainable.
- Keep the execution loop small enough to discuss in interviews.
- Support multiple LLM providers through one interface.
- Keep codebase and filesystem operations constrained by safety checks.

## Execution Flow

1. Receive user task and optional project path/provider/model.
2. Resolve provider and model.
3. Build system prompt with tool descriptions.
4. Ask the LLM for either a final answer or structured JSON action.
5. Parse action and dispatch to Tool Registry.
6. Execute tool and record result.
7. Send tool result back to LLM for final answer.
8. Return answer, tool calls, and references.
