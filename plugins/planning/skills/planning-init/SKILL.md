---
name: planning-init
description: Establish a project planning folder from its existing product, policy, architecture and implementation evidence. Use when migrating project design documents into a planning folder or creating a project's planning baseline.
---

Inspect project instructions, existing documents, code, tests and operational constraints before writing. Identify what is implemented, what is a decision, and what remains undecided; do not invent product policy. Preserve substantive decisions and links during migration, and remove a legacy document only when its contents have a verified destination and references are updated.

Create only the documents the project needs, typically `planning/README.md` as an index, `policy/` for behavior and data rules, `architecture/` for boundaries and technical decisions, and screen or flow documents when relevant. Keep setup and execution in the root README. Describe actual behavior with evidence and distinguish intended changes from current behavior.

Code and planning disagreements are errors to investigate and resolve, not open questions. Put only unresolved policy choices in an open questions section; ask the user when evidence cannot determine a consequential choice. Preserve uncertainty about facts explicitly until verified. Validate document links, claims and any diagrams, then follow the project's verification and Git workflow.
