# Test Plan: Project1

## Project Metadata
- Project Name: Project1
- Iteration: 0.1 (MVP)
- Based on: software-design.md, development-plan.md
- Test Count: 24 (matching development tasks)

---

## Test Strategy

### Testing Philosophy
Tests verify behavior, not implementation. Each test should:
- Be deterministic and repeatable
- Test one specific behavior in isolation
- Include both happy path and edge cases
- Document expected behavior clearly
- Be executable without external dependencies

### Test Categories
- **Unit Tests**: Individual functions and methods
- **Integration Tests**: Component interactions
- **Error Tests**: Failure conditions and edge cases
- **GUI Tests**: User interface behaviors (where applicable)

---

## Phase 1: Core Data Structures and Utilities

### TP:0001 - Test DocElement data structure
**Task Reference**: T:0001

**Unit Tests**:
- Create DocElement with all required fields
- Verify enum values (Kind, File, Status) are properly constrained
- Test serialization/deserialization roundtrip
- Validate field type constraints

**Test Cases**:
```
test_create_valid_doc_element():
  - Create DocElement with valid field values
  - Assert all fields are set correctly
  - Verify enum fields accept only valid values

test_doc_element_serialization():
  - Create DocElement with sample data
  - Serialize to JSON/format
  - Deserialize back to object
  - Assert original equals deserialized

test_invalid_enum_values():
  - Attempt to create DocElement with invalid Kind
  - Assert proper error/validation failure
  - Repeat for File and Status enums
```

**Edge Cases**:
- Empty strings in text fields
- Very long ID strings
- Unicode characters in text fields
- Invalid enum values

---

### TP:0002 - Test PrivilegedRequest data structure
**Task Reference**: T:0002

**Unit Tests**:
- Create PrivilegedRequest with all required fields
- Test timestamp handling (created_at, updated_at)
- Verify argv array storage and retrieval
- Test status transitions

**Test Cases**:
```
test_create_privileged_request():
  - Create request with all fields
  - Verify timestamps are set correctly
  - Assert argv stored as array, not string

test_status_transitions():
  - Create request with pending status
  - Update to approved, running, completed
  - Verify valid state transitions only

test_risk_level_validation():
  - Test all risk levels (low, medium, high)
  - Verify enum constraint enforcement
```

**Edge Cases**:
- Empty argv arrays
- Very large command outputs
- Concurrent status updates
- Invalid status transitions

---

### TP:0003 - Test workspace path resolution
**Task Reference**: T:0003

**Unit Tests**:
- Test home directory expansion (~)
- Verify correct path building for all artifact types
- Test path validation with existing/missing directories

**Test Cases**:
```
test_workspace_root_resolution():
  - Call workspace root function
  - Assert expands ~ to actual home directory
  - Verify appends 'software-projects'

test_project_path_building():
  - Build path for test project 'project1'
  - Assert correct subdirectory structure
  - Test conventions.md, software-design.md paths

test_path_validation():
  - Test with existing workspace directory
  - Test with missing workspace directory
  - Verify appropriate error handling
```

**Edge Cases**:
- Missing home directory
- Permission denied on workspace directory
- Non-existent project names
- Special characters in project names

---

## Phase 2: Markdown Parsing and Document Model

### TP:0004 - Test ID extraction from headings
**Task Reference**: T:0004

**Unit Tests**:
- Extract valid IDs from various heading formats
- Test all supported ID prefixes (R:, C:, D:, etc.)
- Verify heading level detection
- Test ID format validation

**Test Cases**:
```
test_extract_valid_ids():
  - Parse "### R:Purpose" -> {id: "R:Purpose", level: 3}
  - Parse "## C:WorkspaceManager" -> {id: "C:WorkspaceManager", level: 2}
  - Test all prefix types (R:, C:, D:, I:, M:, UI:, T:, TP:)

test_invalid_id_formats():
  - Parse "### Purpose" (no prefix) -> no ID
  - Parse "### R:" (no suffix) -> validation error
  - Parse "### Invalid:Format" -> no ID

test_heading_levels():
  - Test h1 through h6 heading levels
  - Verify correct level number extraction
```

**Edge Cases**:
- Malformed markdown headings
- IDs with special characters
- Duplicate IDs within file
- Very long ID strings

---

### TP:0005 - Test markdown body extraction
**Task Reference**: T:0005

**Unit Tests**:
- Extract body content between headings
- Preserve markdown formatting
- Handle nested heading structures
- Track position information for editing

**Test Cases**:
```
test_extract_simple_body():
  - Markdown with single element
  - Verify complete body content extracted
  - Assert formatting preserved

test_extract_multiple_elements():
  - Markdown with multiple headings/bodies
  - Verify correct boundary detection
  - Assert each element gets correct body

test_position_tracking():
  - Extract element with position info
  - Verify byte/line ranges are accurate
  - Test editing at extracted positions
```

**Edge Cases**:
- Empty element bodies
- Elements with only whitespace
- Nested heading levels
- Elements at end of file

---

### TP:0006 - Test reference detection
**Task Reference**: T:0006

**Unit Tests**:
- Find inline ID references in text
- Parse explicit "References:" sections
- Deduplicate referenced IDs
- Validate referenced IDs exist

**Test Cases**:
```
test_inline_references():
  - Text: "implements C:WorkspaceManager"
  - Assert finds ["C:WorkspaceManager"]
  - Test multiple inline refs in same text

test_explicit_references():
  - Body with "References:\n- R:Purpose\n- C:Parser"
  - Assert finds ["R:Purpose", "C:Parser"]

test_mixed_references():
  - Body with both inline and explicit refs
  - Verify deduplication works correctly
  - Assert returns unique list
```

**Edge Cases**:
- References to non-existent IDs
- Circular reference detection
- References in code blocks (should ignore)
- Multiple "References:" sections

---

### TP:0007 - Test full markdown parsing
**Task Reference**: T:0007

**Integration Tests**:
- Parse complete markdown files
- Handle parsing errors gracefully
- Maintain round-trip editing capability
- Combine all parsing components

**Test Cases**:
```
test_parse_complete_file():
  - Parse sample software-design.md
  - Verify all elements extracted correctly
  - Assert references properly linked

test_parse_error_handling():
  - Parse file with malformed markdown
  - Verify graceful error handling
  - Assert partial results where possible

test_round_trip_editing():
  - Parse file to DocElements
  - Modify element body
  - Save back to file
  - Re-parse and verify changes
```

**Edge Cases**:
- Very large markdown files
- Files with no valid elements
- Binary files passed as markdown
- Encoding issues (UTF-8, etc.)

---

## Phase 3: Workspace Management and Indexing

### TP:0008 - Test workspace discovery
**Task Reference**: T:0008

**Unit Tests**:
- Scan workspace for project directories
- Validate project file structure
- Handle missing required files
- Return project metadata

**Test Cases**:
```
test_discover_valid_projects():
  - Setup workspace with project1/, project2/
  - Run discovery
  - Assert finds both projects with metadata

test_missing_required_files():
  - Setup project missing software-design.md
  - Run discovery
  - Verify error reported appropriately

test_empty_workspace():
  - Point to empty directory
  - Run discovery
  - Assert returns empty project list
```

**Edge Cases**:
- Workspace directory doesn't exist
- Permission denied on workspace
- Projects with partial file sets
- Hidden directories (should ignore)

---

### TP:0009 - Test file system watching
**Task Reference**: T:0009

**Integration Tests**:
- Monitor files for external changes
- Trigger re-parsing on modifications
- Handle watch errors and edge cases

**Test Cases**:
```
test_file_modification_detection():
  - Setup file watcher on test markdown file
  - Modify file externally
  - Assert change event triggered
  - Verify re-parsing initiated

test_file_deletion_handling():
  - Watch existing file
  - Delete file externally
  - Assert deletion event handled gracefully

test_watch_error_recovery():
  - Setup watcher on file
  - Make file unreadable (chmod)
  - Verify error handled without crash
```

**Edge Cases**:
- Rapid successive file changes
- Large file modifications
- Network mounted file systems
- Platform-specific watch limitations

---

### TP:0010 - Test indexer data structures
**Task Reference**: T:0010

**Unit Tests**:
- Test ID -> DocElement mapping performance
- Verify reference graph construction
- Test search index functionality

**Test Cases**:
```
test_id_lookup_performance():
  - Create index with 1000+ elements
  - Time ID lookups
  - Assert O(1) performance characteristics

test_reference_graph():
  - Create elements with cross-references
  - Build reference graph
  - Verify forward and backward links correct

test_search_index():
  - Index elements with varied titles
  - Search for partial title matches
  - Assert relevant results returned
```

**Edge Cases**:
- Duplicate IDs (should error)
- Circular references
- Very large element collections
- Empty search queries

---

### TP:0011 - Test indexer operations
**Task Reference**: T:0011

**Unit Tests**:
- Build initial index from documents
- Update index incrementally
- Maintain referential integrity

**Test Cases**:
```
test_initial_index_build():
  - Parse multiple documents
  - Build complete index
  - Verify all elements indexed correctly

test_incremental_updates():
  - Build initial index
  - Modify one element
  - Update index incrementally
  - Assert only affected elements updated

test_referential_integrity():
  - Create elements with references
  - Delete referenced element
  - Verify backlinks updated correctly
```

**Edge Cases**:
- Index corruption recovery
- Concurrent index updates
- Memory usage with large indexes
- Index persistence across restarts

---

### TP:0012 - Test WorkspaceManager integration
**Task Reference**: T:0012

**Integration Tests**:
- Initialize complete workspace
- Handle file changes end-to-end
- Provide unified workspace operations

**Test Cases**:
```
test_workspace_initialization():
  - Point to test workspace
  - Initialize WorkspaceManager
  - Verify all projects loaded correctly
  - Assert indexes built and watches active

test_end_to_end_file_change():
  - Initialize workspace
  - Modify markdown file externally
  - Verify workspace updates automatically
  - Assert indexes reflect changes

test_workspace_api():
  - Test all public workspace methods
  - Verify consistent behavior
  - Assert proper error handling
```

**Edge Cases**:
- Workspace initialization failures
- File system permission changes
- Network interruptions (if applicable)
- Resource cleanup on shutdown

---

## Phase 4: MCP Tool Server

### TP:0013 - Test MCP read operations
**Task Reference**: T:0013

**Unit Tests**:
- Test list_projects() returns correct data
- Verify list_elements() filtering works
- Test get_element() with various IDs

**Test Cases**:
```
test_list_projects():
  - Setup workspace with test projects
  - Call list_projects()
  - Assert returns correct project list with metadata

test_list_elements_filtering():
  - Call list_elements(project="project1", file="software-design")
  - Verify only software-design elements returned
  - Test kind filtering: list_elements(kind="Task")

test_get_element_by_id():
  - Call get_element(project="project1", id="R:Purpose")
  - Assert returns complete element data
  - Test with non-existent ID returns proper error
```

**Edge Cases**:
- Non-existent projects
- Invalid filter parameters
- Malformed element IDs
- Empty result sets

---

### TP:0014 - Test MCP write operations
**Task Reference**: T:0014

**Unit Tests**:
- Test update_element() modifies correctly
- Verify apply_file_patch() works safely
- Test change summary generation

**Test Cases**:
```
test_update_element():
  - Update element body content
  - Verify change applied to file
  - Assert change summary returned
  - Check original file preserved on error

test_apply_file_patch():
  - Create unified diff patch
  - Apply via apply_file_patch()
  - Verify changes applied correctly
  - Test patch application errors

test_change_auditing():
  - Perform write operation
  - Verify audit log entry created
  - Assert change diff recorded
```

**Edge Cases**:
- Concurrent modifications
- Invalid patch formats
- File permission errors
- Disk space exhaustion

---

### TP:0015 - Test MCP error handling
**Task Reference**: T:0015

**Unit Tests**:
- Test all specified error conditions
- Verify structured error responses
- Test error message quality

**Test Cases**:
```
test_element_not_found():
  - Request non-existent element ID
  - Assert structured error response
  - Verify error message is actionable

test_invalid_id_format():
  - Request element with malformed ID
  - Assert appropriate validation error
  - Check error includes format requirements

test_file_parsing_errors():
  - Corrupt markdown file
  - Trigger parsing operation
  - Verify error handling doesn't crash system
```

**Edge Cases**:
- Network connection errors
- Authentication failures (future)
- Resource exhaustion errors
- Malformed MCP requests

---

### TP:0016 - Test MCP privileged action workflow
**Task Reference**: T:0016

**Integration Tests**:
- Test privileged request creation
- Verify approval status tracking
- Test execution only after approval

**Test Cases**:
```
test_privileged_request_creation():
  - Call sudo_request() with command spec
  - Verify PrivilegedRequest created
  - Assert request_id returned
  - Check request in pending status

test_approval_workflow():
  - Create privileged request
  - Check status with sudo_status()
  - Simulate human approval
  - Verify status updates correctly

test_execution_after_approval():
  - Create and approve request
  - Call sudo_run() with request_id
  - Assert execution only occurs after approval
  - Test execution blocked without approval
```

**Edge Cases**:
- Request timeout handling
- Approval revocation
- Multiple simultaneous requests
- Invalid request specifications

---

## Phase 5: Privileged Action System

### TP:0017 - Test command allowlist management
**Task Reference**: T:0017

**Unit Tests**:
- Test allowlist loading from conventions.md
- Verify command validation against allowlist
- Test allowlist updates and persistence

**Test Cases**:
```
test_allowlist_loading():
  - Setup conventions.md with sample allowlist
  - Load allowlist
  - Verify all commands loaded correctly

test_command_validation():
  - Load test allowlist with /bin/ls, /usr/bin/git
  - Validate /bin/ls -> passes
  - Validate /bin/rm -> fails (not in allowlist)

test_allowlist_updates():
  - Modify allowlist
  - Save changes to conventions.md
  - Reload and verify changes persist
```

**Edge Cases**:
- Malformed allowlist entries
- Missing conventions.md file
- File permission errors on save
- Very large allowlists

---

### TP:0018 - Test privileged request queue
**Task Reference**: T:0018

**Unit Tests**:
- Test request queue persistence
- Verify status updates work correctly
- Test queue management operations

**Test Cases**:
```
test_queue_persistence():
  - Add requests to queue
  - Save queue to disk
  - Reload queue
  - Verify all requests preserved

test_status_updates():
  - Add request in pending state
  - Update status to approved
  - Verify status change persisted
  - Test invalid status transitions rejected

test_queue_operations():
  - Add multiple requests
  - Retrieve by status (pending, approved, etc.)
  - Test queue cleanup (completed requests)
```

**Edge Cases**:
- Queue corruption recovery
- Concurrent queue access
- Disk space issues during persistence
- Queue size limitations

---

### TP:0019 - Test privileged command execution
**Task Reference**: T:0019

**Unit Tests**:
- Test safe command execution (argv only)
- Verify audit logging works correctly
- Test execution error handling

**Test Cases**:
```
test_safe_command_execution():
  - Execute simple command: ["echo", "hello"]
  - Verify no shell invocation
  - Assert stdout captured correctly
  - Check exit code recorded

test_audit_logging():
  - Execute test command
  - Verify audit log entry created
  - Assert log includes: timestamp, argv, cwd, output, exit code
  - Check log immutability

test_execution_errors():
  - Execute non-existent command
  - Verify error handled gracefully
  - Test permission denied scenarios
  - Assert error details in audit log
```

**Edge Cases**:
- Commands that run very long
- Commands with large output
- Commands that require input
- System resource limitations

---

## Phase 6: Basic GUI Framework

### TP:0020 - Test main window layout
**Task Reference**: T:0020

**GUI Tests**:
- Test window creation and layout
- Verify pane organization and resizing
- Test window management operations

**Test Cases**:
```
test_window_creation():
  - Create MainWindow
  - Verify three-pane layout exists
  - Assert tab widget in left pane
  - Check splitters work for resizing

test_pane_organization():
  - Verify left pane contains Design|Code|Test tabs
  - Assert right pane is editor area
  - Check bottom pane for AI Console

test_window_operations():
  - Test window resize behavior
  - Verify close operation works
  - Test minimize/maximize (if applicable)
```

**GUI Testing Notes**:
- May require GUI testing framework
- Consider automated vs manual testing
- Test on multiple screen sizes

---

### TP:0021 - Test navigation pane
**Task Reference**: T:0021

**GUI Tests**:
- Test element list display in each tab
- Verify status indicators work
- Test element selection behavior

**Test Cases**:
```
test_design_tab_display():
  - Load project with design elements
  - Switch to Design tab
  - Verify elements displayed in flat list
  - Assert sorted by ID correctly

test_code_tab_with_status():
  - Load project with tasks in different states
  - Switch to Code tab
  - Verify status indicators displayed
  - Test status visual differentiation

test_element_selection():
  - Click element in navigation pane
  - Verify selection updates editor pane
  - Test selection across different tabs
```

**Edge Cases**:
- Very large element lists (performance)
- Empty projects (no elements)
- Elements with long titles
- Unicode characters in element names

---

### TP:0022 - Test editor pane basic editing
**Task Reference**: T:0022

**GUI Tests**:
- Test element information display
- Verify markdown editing functionality
- Test save operations and undo/redo

**Test Cases**:
```
test_element_display():
  - Select element in navigation
  - Verify ID, title, kind displayed correctly
  - Check references/backlinks shown
  - Assert markdown body loaded in editor

test_markdown_editing():
  - Edit element body content
  - Verify changes reflected immediately
  - Test markdown syntax highlighting (if applicable)
  - Check editor supports standard operations

test_save_and_undo():
  - Edit element body
  - Save changes
  - Verify file updated correctly
  - Test undo/redo functionality
```

**Edge Cases**:
- Very large element bodies
- Special markdown syntax
- Concurrent editing (if applicable)
- File save failures

---

### TP:0023 - Test "Go to ID" navigation
**Task Reference**: T:0023

**GUI Tests**:
- Test ID lookup and navigation
- Verify cross-tab navigation works
- Test error handling for invalid IDs

**Test Cases**:
```
test_valid_id_navigation():
  - Invoke "Go to ID" command
  - Enter valid element ID
  - Verify navigation to correct element
  - Assert appropriate tab activated

test_cross_file_navigation():
  - Navigate to ID in different file
  - Verify correct tab selected
  - Check element highlighted/selected

test_invalid_id_handling():
  - Enter non-existent ID
  - Verify appropriate error message
  - Test malformed ID format handling
```

**Edge Cases**:
- Case sensitivity in IDs
- Partial ID matches
- Navigation during editing
- Performance with large projects

---

### TP:0024 - Test settings dialog
**Task Reference**: T:0024

**GUI Tests**:
- Test conventions.md loading and editing
- Verify save functionality
- Test error handling for file conflicts

**Test Cases**:
```
test_conventions_loading():
  - Open settings dialog
  - Verify conventions.md content loaded
  - Check formatting preserved correctly

test_edit_and_save():
  - Modify conventions content
  - Save changes
  - Verify file updated correctly
  - Test dialog close behavior

test_file_conflict_handling():
  - Open settings with conventions.md
  - Modify file externally while dialog open
  - Attempt to save
  - Verify conflict detection and handling
```

**Edge Cases**:
- Large conventions.md files
- File permission errors
- Concurrent editing scenarios
- Invalid markdown in conventions

---

## Testing Infrastructure

### Test Data Setup
- Sample workspace with test projects
- Mock file system for controlled testing
- Test data generators for large-scale testing

### Test Environment
- Isolated test workspace (not affecting real data)
- Reproducible test conditions
- Automated test data cleanup

### Performance Testing
- Load testing with large projects (1000+ elements)
- Memory usage monitoring during long operations
- Response time validation for interactive operations

### Platform Testing
- Primary: Linux (as specified in requirements)
- Secondary: Consider cross-platform compatibility
- GUI framework specific testing requirements

---

End of test plan.