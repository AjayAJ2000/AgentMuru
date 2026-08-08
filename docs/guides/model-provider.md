# Add a model provider

Implement `ModelProvider` from `agentmuru.models`. Declare accurate capabilities and
translate vendor output into `TextDelta`, `ToolCall`, `ModelCompleted`, or `ModelFailed`.
Never expose vendor response objects to the runtime.

Test streaming order, tool argument normalization, usage, cancellation, rate-limit errors,
and redaction with recorded synthetic fixtures. Keep the provider SDK in an optional extra.
