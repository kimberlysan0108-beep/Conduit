# AI engineering log

Implementation assistance: Codex in ChatGPT Work. No external agents or paid model experiments were invoked.

| Task | Decision | Reason / evidence |
|---|---|---|
| Payment autonomy | Rejected direct model-to-Stripe execution | Ownership, eligibility and authorization are deterministic |
| Workflow | Accepted explicit transitions | Supports auditability and safe pauses |
| First integration run | Fixed Customer ownership lookup | Customer table owns itself; it has no customer_id column |
| Stripe adapter | Fixed SDK object conversion | Installed SDK resource object was not dict-iterable |
| Pending external outcomes | Block other customer mutations until reconciled | Prevent spending through an unknown provider response |
| Idempotency | Bound key to stable case + plan; limit old unknown retries | Duplicate and provider-retention risks |
| Credits | Added aggregate exception cap | New request IDs must not multiply exception value |
| Benchmarks | Rejected presenting rule baseline as an LLM experiment | No live LLM credentials used |
| Retrieval | Rejected calling TF-IDF semantic embeddings | Explicit offline vector baseline label |
| Deployment | Rejected claiming a hosted URL without deployment | Docker-ready local demo only |

The brief discourages asking an agent to build the entire project. This delivery follows the user's explicit request for end-to-end implementation, while documenting design choices and testing concrete invariants. It does not replace the intern's independent research, external experiments, operator study, or explanation of engineering choices.
