---
name: planning-diagram
description: Create or update editable project flow diagrams and screen wireframes from planning documents and verified behavior. Use for draw.io flows or Excalidraw wireframes, not finished product UI design.
---

Read the relevant policies, screens and implementation evidence. Represent the requested flow or screen states without inventing features. Keep node labels and numbering aligned with the planning documents, include decision paths and failure states when relevant, and retain editable source files. Do not overwrite existing diagrams without inspecting them first.

For programmatic generation, `scripts/flow.py` provides `Flow.node`, `Flow.edge`, and `Flow.save(path, title)`; `scripts/board.py` provides `Board` drawing methods and `Board.save(path)`. Import them from a short project-specific generator; they contain no project content. Inspect their signatures before use. Use native editors when they fit better.

Validate the generated XML or JSON, unique IDs and edge references; render in the appropriate viewer and inspect layout, text, clipping and connections when a rendering environment is available. Report any unavailable visual verification. For screenshots of a running app, follow that project's own test and privacy constraints; do not fabricate authenticated data or send private data to third parties.
