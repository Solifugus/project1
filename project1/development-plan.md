# Development Plan: Project1

## Project Metadata
- Project Name: Project1
- Iteration: 0.1 (MVP)
- Based on: software-design.md
- Task Count: 24

---

## Phase 1: Core Data Structures and Utilities

### T:0001 - Define DocElement data structure
**Goal**: Implement the core DocElement struct/class as specified in D:DocElement

**References**: D:DocElement

**Implementation**:
- Create DocElement with all specified fields (id, kind, title, file, heading_level, anchor, body_markdown, refs, backlinks, status)
- Define Kind enum: {Requirement, Component, Data, Interface, Method, UI, Task, Test, Other}
- Define File enum: {conventions, software-design, development-plan, test-plan}
- Define Status enum: {pending, in_progress, completed}

**Outputs**: DocElement data structure definition

**Acceptance Criteria**:
- All fields present and correctly typed
- Enums properly defined
- Structure is serializable for persistence

---

### T:0002 - Define PrivilegedRequest data structure
**Goal**: Implement PrivilegedRequest struct/class as specified in D:PrivilegedRequest

**References**: D:PrivilegedRequest

**Implementation**:
- Create PrivilegedRequest with all specified fields
- Define Status enum: {pending, approved, denied, running, completed, failed}
- Define RiskLevel enum: {low, medium, high}
- Define CreatedBy enum: {AI, Human}

**Outputs**: PrivilegedRequest data structure definition

**Acceptance Criteria**:
- All fields present with correct types
- Timestamp handling for created_at, updated_at
- Result field can store command outputs

---

### T:0003 - Implement workspace path resolution
**Goal**: Create utility to resolve standard workspace paths

**References**: R:WorkspaceLayout

**Implementation**:
- Function to resolve ~/software-projects as workspace root
- Functions to build paths: conventions.md, project subdirs, artifact files
- Path validation and existence checking

**Outputs**: Path utility functions

**Acceptance Criteria**:
- Correctly expands ~ to home directory
- Validates workspace structure
- Returns proper paths for all artifact types

---

## Phase 2: Markdown Parsing and Document Model

### T:0004 - Implement ID extraction from headings
**Goal**: Parse markdown headings and extract element IDs

**References**: R:IDConvention, C:MarkdownParser

**Implementation**:
- Regex or parser to identify headings with ID format
- Extract ID prefix and number/name from heading text
- Validate ID format against conventions
- Handle heading levels (h1, h2, h3, etc.)

**Outputs**: ID extraction function

**Acceptance Criteria**:
- Correctly identifies R:, C:, D:, I:, M:, UI:, T:, TP: prefixes
- Validates project-scoped uniqueness
- Returns heading level information

---

### T:0005 - Implement markdown body extraction
**Goal**: Extract element body content between headings

**References**: C:MarkdownParser

**Implementation**:
- Parse markdown to identify heading boundaries
- Extract body content from current heading to next same/higher level
- Preserve original markdown formatting
- Track byte/line ranges for editing

**Outputs**: Body extraction function

**Acceptance Criteria**:
- Correctly identifies element boundaries
- Preserves formatting and whitespace
- Returns position information for editing

---

### T:0006 - Implement reference detection
**Goal**: Find ID references within element bodies

**References**: R:ReferenceFormat, C:MarkdownParser

**Implementation**:
- Scan body text for inline ID mentions (e.g., "implements C:WorkspaceManager")
- Parse explicit "References:" sections
- Extract unique list of referenced IDs
- Validate referenced IDs exist

**Outputs**: Reference extraction function

**Acceptance Criteria**:
- Finds both inline and explicit references
- Returns deduplicated list of valid IDs
- Handles multiple reference formats

---

### T:0007 - Implement full markdown parsing
**Goal**: Combine parsing components into complete markdown-to-DocElement converter

**References**: C:MarkdownParser

**Implementation**:
- Integrate ID extraction, body extraction, and reference detection
- Parse entire markdown files into lists of DocElements
- Handle parsing errors gracefully
- Maintain round-trip editing capability

**Outputs**: MarkdownParser class

**Acceptance Criteria**:
- Parses complete markdown files
- Returns well-formed DocElement objects
- Preserves enough information for saving back to file
- Handles malformed markdown gracefully

---

## Phase 3: Workspace Management and Indexing

### T:0008 - Implement workspace discovery
**Goal**: Scan workspace directory to find projects and required files

**References**: C:WorkspaceManager

**Implementation**:
- Scan ~/software-projects for subdirectories
- Check for required files: conventions.md, software-design.md, etc.
- Validate project structure
- Return project metadata

**Outputs**: Workspace discovery methods

**Acceptance Criteria**:
- Finds all valid project directories
- Identifies missing required files
- Returns structured project information

---

### T:0009 - Implement file system watching
**Goal**: Monitor markdown files for external changes

**References**: C:WorkspaceManager

**Implementation**:
- Set up file system watchers on markdown files
- Detect file modifications, additions, deletions
- Trigger re-parsing when files change
- Handle watch errors and edge cases

**Outputs**: File watching functionality

**Acceptance Criteria**:
- Detects external file changes
- Triggers appropriate re-indexing
- Handles file operations safely

---

### T:0010 - Implement indexer data structures
**Goal**: Create efficient lookup maps for elements and references

**References**: C:Indexer

**Implementation**:
- ID -> DocElement mapping
- File -> elements mapping
- Reference graph (refs and backlinks)
- Search index for titles and IDs

**Outputs**: Indexer storage structures

**Acceptance Criteria**:
- Fast O(1) ID lookups
- Efficient reference graph traversal
- Search index supports partial matching

---

### T:0011 - Implement indexer operations
**Goal**: Build and maintain index structures

**References**: C:Indexer

**Implementation**:
- Build initial index from parsed documents
- Update index incrementally when files change
- Compute backlinks from reference graph
- Maintain search index consistency

**Outputs**: Indexer class with update methods

**Acceptance Criteria**:
- Builds complete index from scratch
- Updates efficiently on changes
- Maintains referential integrity

---

### T:0012 - Integrate WorkspaceManager components
**Goal**: Combine discovery, parsing, watching, and indexing

**References**: C:WorkspaceManager

**Implementation**:
- Initialize workspace from directory scan
- Parse all markdown files on startup
- Set up file watching for continuous updates
- Provide unified interface for workspace operations

**Outputs**: Complete WorkspaceManager class

**Acceptance Criteria**:
- Loads workspace successfully on startup
- Maintains consistency with file changes
- Provides clean API for workspace operations

---

## Phase 4: MCP Tool Server

### T:0013 - Implement MCP read operations
**Goal**: Expose read-only operations for external AI agents

**References**: C:MCPServer

**Implementation**:
- list_projects() - return available projects
- list_elements(project, file, kind) - return filtered element lists
- get_element(project, id) - return specific element details

**Outputs**: MCP read operation handlers

**Acceptance Criteria**:
- Returns properly structured data
- Handles filtering parameters correctly
- Provides comprehensive element information

---

### T:0014 - Implement MCP write operations
**Goal**: Allow external agents to modify elements safely

**References**: C:MCPServer, R:MCPNoSilentWrites

**Implementation**:
- update_element(project, id, patch) - modify element content
- apply_file_patch(project, file, unified_diff) - apply file-level changes
- Return change summaries and diffs

**Outputs**: MCP write operation handlers

**Acceptance Criteria**:
- Applies changes safely with validation
- Returns clear change summaries
- Maintains file integrity

---

### T:0015 - Implement MCP error handling
**Goal**: Return structured errors for common failure cases

**References**: R:MCPErrorHandling

**Implementation**:
- Element not found errors
- Invalid ID format errors
- File parsing errors
- Permission denied errors
- Structured error response format

**Outputs**: Error handling framework

**Acceptance Criteria**:
- All error cases return structured responses
- Error messages are actionable
- Consistent error format across operations

---

### T:0016 - Implement MCP privileged action workflow
**Goal**: Support privileged command requests and execution

**References**: C:MCPServer, D:PrivilegedRequest

**Implementation**:
- sudo_request(project, request_spec) -> request_id
- sudo_status(project, request_id) - check approval status
- sudo_run(project, request_id) - execute after approval

**Outputs**: Privileged action MCP endpoints

**Acceptance Criteria**:
- Creates proper PrivilegedRequest objects
- Tracks request state accurately
- Integrates with approval workflow

---

## Phase 5: Privileged Action System

### T:0017 - Implement command allowlist management
**Goal**: Load and validate allowlisted commands

**References**: R:AllowlistManagement

**Implementation**:
- Parse allowlist from conventions.md
- Validate command paths against allowlist
- Provide allowlist editing interface
- Handle allowlist updates

**Outputs**: Allowlist management functions

**Acceptance Criteria**:
- Loads allowlist from conventions.md
- Validates commands correctly
- Supports safe allowlist updates

---

### T:0018 - Implement privileged request queue
**Goal**: Store and manage pending privileged requests

**References**: C:PrivilegedRequestQueue

**Implementation**:
- Add requests to queue
- Update request status
- Persist queue to disk (project-local)
- Retrieve requests by status

**Outputs**: PrivilegedRequestQueue class

**Acceptance Criteria**:
- Persists requests across application restarts
- Maintains request state correctly
- Provides queue management operations

---

### T:0019 - Implement privileged command execution
**Goal**: Safely execute approved privileged commands

**References**: C:PrivilegedHelper, R:NoShellRoot, R:AuditLog

**Implementation**:
- Execute commands as argv arrays (no shell)
- Capture stdout, stderr, exit codes
- Write immutable audit log entries
- Handle execution errors safely

**Outputs**: PrivilegedHelper class

**Acceptance Criteria**:
- Never invokes shell for command execution
- Captures complete execution results
- Maintains immutable audit trail

---

## Phase 6: Basic GUI Framework

### T:0020 - Implement main window layout
**Goal**: Create basic application window structure

**References**: C:MainWindow

**Implementation**:
- Left pane: tab widget (Design | Code | Test)
- Right pane: editor/inspector area
- Bottom pane: AI Console + Privileged Requests
- Basic window management (resize, close)

**Outputs**: MainWindow class with layout

**Acceptance Criteria**:
- Three-pane layout as specified
- Proper tab widget in left pane
- Resizable panes with splitters

---

### T:0021 - Implement navigation pane
**Goal**: Display flat lists of elements by type

**References**: C:NavigationPane

**Implementation**:
- Design tab: flat list of design elements sorted by ID
- Code tab: flat list of tasks with status indicators
- Test tab: flat list of test entries sorted by ID
- Element selection and navigation

**Outputs**: NavigationPane class

**Acceptance Criteria**:
- Displays elements in flat lists as specified
- Shows task status indicators
- Supports element selection

---

### T:0022 - Implement editor pane with basic editing
**Goal**: View and edit selected elements

**References**: C:EditorPane

**Implementation**:
- Display element ID, title, kind, references/backlinks
- Markdown editor for body content
- Save element changes back to file
- Basic undo/redo functionality

**Outputs**: EditorPane class

**Acceptance Criteria**:
- Shows complete element information
- Edits markdown body safely
- Implements undo/redo stack

---

### T:0023 - Implement "Go to ID" navigation
**Goal**: Direct navigation to any element by ID

**References**: C:EditorPane

**Implementation**:
- Command/dialog to enter target ID
- Lookup element by ID using indexer
- Navigate to element across tabs/files
- Handle invalid IDs gracefully

**Outputs**: Navigation command functionality

**Acceptance Criteria**:
- Finds elements by exact ID match
- Switches tabs/views as needed
- Provides clear feedback for invalid IDs

---

### T:0024 - Implement settings dialog
**Goal**: Edit global conventions

**References**: C:SettingsDialog

**Implementation**:
- Load conventions.md content
- Provide editing interface
- Save changes back to conventions.md
- Handle editing conflicts/errors

**Outputs**: SettingsDialog class

**Acceptance Criteria**:
- Loads current conventions correctly
- Saves changes safely
- Handles file edit conflicts

---

## Implementation Notes

### Development Order
Tasks are ordered to minimize dependencies:
- Phases 1-3 can be developed and tested independently
- Phase 4 requires Phases 1-3 for workspace access
- Phase 5 requires Phase 4 for MCP integration
- Phase 6 requires Phases 1-4 for data access

### Testing Strategy
Each task should include:
- Unit tests for core functionality
- Integration tests for component interactions
- Manual testing for GUI components

### Technology Choices
- Programming language: TBD (Python, Rust, Go, or similar)
- GUI framework: TBD (based on language choice)
- MCP implementation: Follow MCP specification
- File watching: Platform-appropriate file system events

---

End of development plan.