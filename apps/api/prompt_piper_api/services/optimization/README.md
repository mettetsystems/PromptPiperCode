# Token optimization (`services/optimization/`)

Five-pass local optimizer run after finalization on coding-prompt drafts. Rebuilds the six coding-dimension section contract. Produces `OptimizationResult` for the approval gate and export.

| Pass | Module | What it does |
|------|--------|--------------|
| 1 | `constraint_graph_pass.py` | Slot coding-card + body requirements into typed constraint graph; detect contradictions |
| 2 | `rewrite_pass.py` | Rebuild six coding sections; merge duplicates |
| 3 | `denoising_pass.py` | Remove repetition and filler (protects binding phrases) |
| 4 | `deconfliction_pass.py` | Resolve or flag hard conflicts |
| 5 | `binding_preservation_pass.py` | Re-inject binding requirements into Architectural Rules when missing after compression |
| — | `metrics.py` | Token metrics and `ApprovalExportPass` packaging |
| — | `engine.py` | `TokenOptimizationEngine.optimize()` orchestration |

Approval scoring uses **binding phrases** from the constraint graph (see `requirement_capture.collect_optimization_binding_phrases`), not every optional requirement-card leaf.

**Semantic precision** is evaluated separately in `semantic_precision.py` and surfaced on the Optimize step; optional LLM-guided refinement runs via `/sessions/{id}/precision/*` when score is below 0.75 and a model is available.
