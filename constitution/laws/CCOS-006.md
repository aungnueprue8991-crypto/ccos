# CCOS-006 — All consequential actions must be observable

**Status**: Active
**Version**: 1.0
**Plane**: Observatory

## Statement
Every capability invocation, governance decision, memory write, and external action must emit a typed EventEnvelope that is persisted in the Observatory ledger before or atomically with the action.
