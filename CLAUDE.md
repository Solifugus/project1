# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Project1** is a GUI + MCP tool server for AI-assisted software development. Currently in design phase (MVP 0.1) - no implementation code exists yet. The project follows a design-first, artifact-based workflow where structured documents replace conversational context for AI collaboration.

**Core Innovation**: Treats software design, development plans, and test plans as addressable, queryable artifacts with stable IDs, enabling AI to work with precise context rather than large conversation histories.

## Project Status

This is currently a **design-first repository**:
- All architectural decisions are documented in `project1/software-design.md`
- Implementation will follow once design is complete
- Focus on understanding the artifact-based workflow philosophy

## Key Concepts

### Artifact-Based Workflow
1. **software-design.md** - Structured design with addressable elements (R:, C:, D:, I:, M:, UI: prefixes)
2. **development-plan.md** - Atomic tasks (T:#### IDs) derived from design
3. **test-plan.md** - Test specifications (TP:#### IDs) keyed to tasks
4. **Code** - Final implementation following the above artifacts

### ID Conventions
- `R:####` - Requirements
- `C:####` - Components
- `D:####` - Data Structures
- `I:####` - Interfaces
- `M:####` - Methods
- `UI:####` - UI Elements
- `T:####` - Development Tasks
- `TP:####` - Test Plans

## Development Philosophy

From `conventions.md` and `pholosophy.md`:

### Coding Standards
- Prefer clarity over cleverness
- Prefer explicitness over inference
- Functions should do one thing
- Handle errors deliberately, never silently
- No unused code or commented-out blocks

### AI Collaboration Rules
- AI executes well-defined tasks, doesn't invent architecture
- Each task must be executable in a fresh session
- Context assembled on-demand from stable artifacts, not conversation history
- Humans maintain control over design decisions

## Architecture Overview

**Planned Components** (from `project1/software-design.md`):

### Backend
- **Workspace Manager** - Load and validate project structure
- **Markdown Parser** - Parse documents into addressable elements
- **Indexer** - Build lookup maps for IDs and references
- **MCP Server** - Expose tools to external AI agents
- **Privileged Helper** - Execute approved commands with audit logging

### GUI (Desktop Application)
- **MainWindow** - Tabbed interface (Design | Code | Test)
- **NavigationPane** - Tree views of elements and tasks
- **EditorPane** - Edit documents with live preview
- **AIConsole** - Chat interface with draft/apply workflow
- **SettingsDialog** - Edit global conventions

## Workspace Structure

```
<workspace>/
├── conventions.md          # Global coding/collaboration standards
├── pholosophy.md          # Design philosophy
├── <project-name>/
│   ├── software-design.md  # Structured design with stable IDs
│   ├── development-plan.md # Atomic task breakdown
│   └── test-plan.md        # Test specifications
└── templates/             # Templates for new projects
```

## Security Model

- GUI runs unprivileged
- Privileged actions require explicit human approval
- Commands executed as argv arrays (no shell injection)
- Allowlist-only for privileged operations
- Immutable audit logging of all privileged commands

## Development Approach

### When Implementation Begins
1. Build according to `project1/software-design.md` specifications
2. Each component has explicit ID, interface, and responsibility
3. Create atomic tasks in `development-plan.md` before coding
4. Never modify unrelated components
5. Test specifications must exist before implementation

### Task Execution
- Tasks should be method-sized when possible
- Each task contains all required context
- Reference design elements by their stable IDs
- Prefer asking for clarification over guessing

## Key Files to Understand

1. **`conventions.md`** - Non-negotiable coding and collaboration standards
2. **`pholosophy.md`** - Why this artifact-based approach exists
3. **`project1/software-design.md`** - Complete system specification with component IDs
4. **`templates/`** - Standard structure for new projects

## Important Notes

- This is not a traditional codebase - it's a meta-tool for building software
- Design completeness is prioritized over speed to implementation
- All architectural decisions must be explicit in design documents
- AI should never invent requirements or modify the core design philosophy