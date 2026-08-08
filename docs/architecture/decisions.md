# Architecture decisions

## Runtime first

Agent execution is the application. UI is a projection so runtime tests need no browser.

## Events before rendering

Events support streaming, replay, observability, and multiple consumers without frontend coupling.

## Explicit sessions

Sessions define ownership and persistence boundaries; no global mutable application state exists.

## Provider neutrality

Normalized model events keep vendor SDK semantics outside agents and runtime code.

## Governed tools

Permissions and approvals exist because Python callbacks are not an adequate enterprise security model.

## First-class artifacts

AI applications produce structured work, not only chat text. Artifacts have stable identities and storage.
