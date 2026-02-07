# Software Design: Project1

## Project Metadata
- Project Name: Project1
- Iteration: 0.1 (MVP)
- Purpose: A GUI + MCP tool server that helps a human and AI collaborate to produce software designs, development plans, and test plans as structured, addressable artifacts, and to execute work via small, self-contained task packets.
- Scope: Local workspace tool. No cloud dependency required. Supports AI via external driver (Claude Code) and later pluggable providers (including local models).

---

## 0. Intent and Constraints

### R:Purpose
Project1 provides a disciplined workflow for building software with AI by keeping design intent explicit, decomposing work into atomic tasks, and ensuring each task contains sufficient context to execute in a fresh session with minimal context window.

### R:Audience
- Primary: Matthew (solo developer) collaborating with AI systems
- Secondary: Small teams adopting the same artifact-based workflow

### R:Scope
In scope:
- Project workspace management (projects folder + per-project files)
- Edit/view software design, dev plan, and test plan
- Parse documents into addressable elements by ID
- Expose MCP tool interface to read/update/generate artifacts
- Privileged actions via explicit human approval and allowlisted execution
- AI assistance through Claude Code (external) and optional internal providers

Out of scope (MVP):
- Full IDE (debugger, language server, refactoring of codebase)
- Project compilation/build orchestration beyond simple commands
- Multi-user collaboration and syncing
- Deep GitHub automation (PR creation, CI, etc.)

### R:Stability
- Must operate reliably on Linux (primary target)
- Files remain plain Markdown and human-readable
- No fragile proprietary formats as the source of truth

### R:Security
- GUI must run unprivileged
- Privileged operations must require explicit human approval
- No shell execution as root
- All privileged actions logged with command argv, output, and exit code

### R:Performance
- Must handle projects with hundreds to thousands of design/task/test elements
- Search and selection must be responsive (<100ms target for common actions)

---

## 1. Workspace Model

### R:WorkspaceLayout
Workspace layout:
- `<workspace>/conventions.md` (global conventions)
- `<workspace>/<project-name>/software-design.md`
- `<workspace>/<project-name>/development-plan.md`
- `<workspace>/<project-name>/test-plan.md`
- Additional generated folders (later): `src/`, `tests/`, etc.

### C:WorkspaceManager
Purpose: Load, validate, and index the workspace and projects.
Responsibilities:
- Discover projects in the workspace
- Ensure required files exist
- Provide paths, metadata, and indexing state
- Monitor markdown files for external changes and trigger re-indexing

---

## 2. Document Model and IDs

### R:IDConvention
All addressable elements must have stable IDs, expressed in Markdown headings.
Recommended prefixes:
- Design elements: `R:`, `C:`, `D:`, `I:`, `M:`, `UI:`
- Dev tasks: `T:####`
- Tests: `TP:####`

IDs must be unique across all files within a project (project-scoped uniqueness).

### R:ReferenceFormat
Elements reference other elements by bare ID (e.g., "implements C:WorkspaceManager", "see R:Purpose").
References are detected through:
- Explicit "References:" sections within element body
- Inline ID mentions in element body text

### R:Addressability
Each element must be retrievable by:
- ID
- Markdown anchor (derived from heading)
- File + byte/line range (internal)

### D:DocElement
Fields:
- id: string
- kind: enum {Requirement, Component, Data, Interface, Method, UI, Task, Test, Other}
- title: string
- file: enum {conventions, software-design, development-plan, test-plan}
- heading_level: int
- anchor: string
- body_markdown: string
- refs: list[string] (IDs referenced in body or in explicit "References" section)
- backlinks: list[string] (computed)
- status: enum {pending, in_progress, completed} (for Task kind only)

### C:MarkdownParser
Purpose: Parse Markdown files into DocElements and preserve round-trip edits.
Responsibilities:
- Identify headings and extract ID + title
- Capture body ranges
- Maintain stable rewrite behavior when saving
- Extract references (explicit and/or heuristic)

### C:Indexer
Purpose: Build fast lookup maps for IDs and references.
Responsibilities:
- id -> DocElement
- file -> elements
- ref graph (refs and backlinks)
- search index for titles and IDs

---

## 3. GUI

### C:MainWindow
Layout:
- Left pane: tab widget with three tabs: Design | Code | Test
- Right pane: editor/inspector (Markdown editor + optional preview)
- Bottom pane: AI Console + Privileged Requests tray

### C:NavigationPane
Design tab:
- Flat list of design elements sorted by ID
Code tab:
- Flat list of tasks (T:####) sorted by ID, with status indicators
Test tab:
- Flat list of test entries sorted by ID

### C:EditorPane
Purpose: View/edit the selected element.
Responsibilities:
- Show ID, title, kind, references/backlinks
- Edit Markdown body
- Save element back into file safely
- Undo/redo stack for reverting AI suggestions
- "Go to ID" command for direct navigation to any element
- Provide "Packet Preview" for selected tasks (optional)

### C:AIConsole
Purpose: Human-AI collaboration with safe application of changes.
Responsibilities:
- Chat transcript (per project)
- Context-aware prompts (based on current selection)
- “Draft vs Apply” workflow:
  - Draft: propose changes
  - Apply: show diff and apply only with explicit confirmation

### C:SettingsDialog
Purpose: Edit and manage `conventions.md`.
Responsibilities:
- Open global conventions
- Optionally support project overrides later

---

## 4. AI Integration

### R:AIIntegrationModes
Project1 MVP focuses on external driver mode only:
- Claude Code calls Project1 MCP tools to read/write/generate artifacts
- Human-AI collaboration occurs through the AI Console with draft/apply workflow

### R:ContextAssembly
When AI requests context for operations:
- Selected element and its direct references are included
- Conventions.md content is included
- Context is assembled on-demand from current artifact state, not conversation history

Future work: Internal provider mode where Project1 calls AI providers directly

---

## 5. MCP Tool Server

### C:MCPServer
Purpose: Expose Project1 capabilities as MCP tools to external agents (Claude Code).
Responsibilities:
- Provide read operations:
  - list_projects()
  - list_elements(project, file, kind)
  - get_element(project, id)
- Provide write operations:
  - update_element(project, id, patch)
  - apply_file_patch(project, file, unified_diff)
- Provide generation operations:
  - generate_plan(project, options)
  - generate_tests(project, options)
- Provide privileged action workflow:
  - sudo_request(project, request_spec) -> request_id
  - sudo_status(project, request_id)
  - sudo_run(project, request_id) (only after human approval)

### R:MCPNoSilentWrites
All writes must be explicit and traceable. Prefer diffs/patches.
Any tool call that modifies files must:
- return a summary of changes
- optionally return a diff
- update audit logs

### R:MCPErrorHandling
MCP tools must return structured error responses for common failure cases:
- Element not found (invalid ID)
- Invalid ID format
- File parsing errors
- Project not found
- Permission denied
- File system errors

---

## 6. Privileged Actions (Approved Sudo)

### R:HumanApprovalRequired
No privileged command may run without explicit human approval in the GUI.

### R:NoShellRoot
Privileged commands must be executed without invoking a shell. Commands are argv arrays only.

### R:AllowlistOnly
Only allowlisted commands may be executed as privileged actions.

### R:AllowlistManagement
Command allowlist is stored in `conventions.md` under a "Privileged Commands" section.
Allowlist entries specify command paths and brief justifications.
Allowlist can be edited through the Settings Dialog.

### D:PrivilegedRequest
Fields:
- request_id: string (PR:####)
- title: string
- reason: string
- commands: list[list[string]] (argv)
- verification: list[list[string]] (argv)
- risk_level: enum {low, medium, high}
- created_by: enum {AI, Human}
- related_task_id: optional string
- status: enum {pending, approved, denied, running, completed, failed}
- created_at, updated_at timestamps
- result: stdout/stderr/exit code per command

### C:PrivilegedRequestQueue
Purpose: Store and display pending requests.
Responsibilities:
- Add request
- Update status
- Persist to disk (project-local)

### C:PrivilegedHelper
Purpose: Execute approved privileged requests safely.
Responsibilities:
- Validate argv against allowlist
- Execute commands as root (via pkexec/sudo mechanism)
- Capture stdout/stderr and exit codes
- Write immutable audit log entries
- Return structured results

### R:AuditLog
All privileged executions must be logged:
- timestamp
- request_id
- argv
- cwd
- stdout/stderr
- exit code
- approving user

---

## 7. Generation Workflows

### R:GenerateDevelopmentPlan
Given `software-design.md` + `conventions.md`, Project1 can generate or update `development-plan.md` such that:
- tasks are small (method-sized when possible)
- each task includes:
  - goal
  - references to design IDs
  - outputs (files)
  - acceptance criteria
  - test references

### R:GenerateTestPlan
Given `software-design.md` + `development-plan.md` + `conventions.md`, Project1 can generate or update `test-plan.md` such that:
- each task has matching tests
- tests reflect acceptance criteria and edge cases

### R:Revisions
Project1 must support revising:
- design elements
- tasks
- tests
with AI assistance and diff-based application.

---

## 8. Non-Goals and Future Work

Future work:
- Internal AI provider mode (Project1 calls AI providers directly)
- AIProvider interface with generate_plan/test methods
- Tree/hierarchical organization in NavigationPane (vs. flat lists)
- Packet export (single text blob per task)
- Git integration (commit messages referencing task IDs)
- Local model integration (Ollama/vLLM) behind AIProvider
- Advanced consistency auditing (orphan IDs, missing tests, circular refs)
- Import/export templates for new projects
- Task dependency tracking and ordering
- Concurrent edit detection and resolution

---

End of software design.