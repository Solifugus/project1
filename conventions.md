# Conventions

This document defines global conventions that apply across all projects in this workspace.
Project-specific documents must not override these conventions unless explicitly stated.

---

## 1. Author & Identity
- Author: Matthew Tedder
- Preferred license: MIT (unless otherwise specified)
- Default repository hosting: GitHub

---

## 2. Coding Philosophy
- Prefer clarity over cleverness
- Prefer explicitness over inference
- Functions and methods should do one thing
- Side effects must be obvious from the interface
- Errors should be handled deliberately, not implicitly

---

## 3. Coding Style (General)
- Use descriptive names; avoid abbreviations unless standard
- Avoid deeply nested logic
- Prefer pure functions where possible
- Document non-obvious decisions inline
- No unused code or commented-out blocks

(Language-specific conventions may be added per project.)

---

## 4. Error Handling
- Expected failure cases are handled explicitly
- Unexpected failures should fail loudly
- Never silently swallow errors
- Error messages must be actionable

---

## 5. Testing Philosophy
- Tests are first-class artifacts
- Each unit of behavior must be testable in isolation
- Tests should be deterministic
- Tests should document intent, not implementation details

---

## 6. Documentation Expectations
- Public interfaces must be documented
- Internal complexity should be explained where it exists
- Design decisions should be recorded, not inferred

---

## 7. Git & GitHub Essentials
- Branch naming: `feature/<short-name>`, `fix/<short-name>`
- Commits:
  - Small, focused, descriptive
  - One logical change per commit
- Pull Requests:
  - Must reference task IDs
  - Must pass tests
  - Must include a short rationale

---

## 8. AI Collaboration Rules
- AI-generated code must meet the same standards as human-written code
- If assumptions are made, they must be stated explicitly
- AI should not modify unrelated files
- AI should prefer asking for clarification over guessing

---

End of conventions.
