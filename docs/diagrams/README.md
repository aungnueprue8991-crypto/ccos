# NEXUS diagrams

## Anomaly → Discovery state machine

| File | Content |
|------|---------|
| `anomaly_discovery_state.mmd` | Full runtime control loop (TB) |
| `anomaly_discovery_events.mmd` | Same loop with event names (LR) |
| `four_layer_architecture.mmd` | Reality → CCOS → NEXUS → Evolution |

### Render locally

```bash
npx -y @mermaid-js/mermaid-cli -i docs/diagrams/anomaly_discovery_state.mmd -o docs/diagrams/anomaly_discovery_state.svg
npx -y @mermaid-js/mermaid-cli -i docs/diagrams/anomaly_discovery_events.mmd -o docs/diagrams/anomaly_discovery_events.svg
npx -y @mermaid-js/mermaid-cli -i docs/diagrams/four_layer_architecture.mmd -o docs/diagrams/four_layer_architecture.svg
```

### Maps to code

| State / transition | Code |
|--------------------|------|
| `AnomalyCheck` / `BroadcastAnomaly` | `nexus/routing/rules.py` → `anomaly_rule` |
| `ThoughtQuestion` | `CognitiveEcology.step_thought_question` |
| `HypothesisSpace` / `TheoryCompetition` | `step_hypothesis_competition` |
| `Experiment` / `EvidenceGate` | `step_experiment_evidence` |
| Event types | `nexus/workspace/events.py` → `CogEventType` |
| Workspace broadcast | `nexus/workspace/blackboard.py` → `GlobalWorkspace` |

### How to read

1. **Observation** starts the loop.
2. **Prediction mismatch** → anomaly score.
3. Above threshold → **broadcast** to Question, Pattern, Memory, Curiosity (parallel).
4. Outputs feed **HypothesisSpace** → competition → prediction → simulation → experiment.
5. **Evidence gate**: support / falsify / inconclusive.
6. Support → abstraction → transfer → meta policy → back to observation.
7. Falsify → hypothesis evolution → search again.
