# CCOS-005 — No subsystem may silently modify another subsystem's authoritative state

**Status**: Active
**Version**: 1.0
**Plane**: All

## Statement
State ownership is exclusive. Communication occurs only through typed contracts and the event substrate. Direct database or memory writes across subsystem boundaries are forbidden.
