# CLAUDE.md - Universal Standing Instructions

This document contains universal standing instructions for AI assistants working on any software project. These instructions are project-agnostic and can be applied across different codebases.

---

## 🔴 EXPLICIT STANDING INSTRUCTIONS (Required)

These instructions MUST be followed when working on any software project:

*****ALWAYS keep claude_continue.md continuously updated, using **correct** timestamps, so that users and claude code sessions can resume immediately with full confidence in the event of an IDE crash or windows crash/.restart******


### 1. Tool & Agent Awareness
- **STAY AWARE** of all available subagents at all times
- **PROACTIVELY USE** relevant subagents without being asked when appropriate
- **STAY AWARE** of all available MCPs (Model Context Protocols)
- **PROACTIVELY USE** relevant MCPs when they can improve task completion
- **MANDATORY**: Use `mcp__sequentialthinking__sequentialthinking` for complex analysis and planning
- **MANDATORY**: Use `TodoWrite` tool for continuous progress tracking on multi-step tasks

### 2. Code Organization & Quality
- **KEEP** repository structure logical, organized, and neat
- **ENSURE** all code includes useful and understandable comments for both humans and AI
  - Comments should explain WHY, not just WHAT
  - Complex logic should be thoroughly documented
  - API interactions should include example requests/responses in comments
- **ENFORCE** file and script naming conventions that are concise but understandable
  - Use descriptive names that clearly indicate purpose and functionality
  - Employ sequential naming (01_, 02_, 03_) for workflow scripts when appropriate
  - Avoid ambiguous or overly abbreviated names that require context to understand
- **REMOVE** scripts or documentation files that are replaced by newer versions
  - Maintain an explicit log file detailing what files are removed
  - Document commit/branch/repo information for recovery if needed
  - Preserve removal context for later human/AI understanding
- **PERIODICALLY RE-EVALUATE** repository structure and imports using appropriate subagents
  - Use code-reviewer and architect-reviewer agents to assess organization
  - Identify redundant functionality and consolidation opportunities
  - Ensure logical grouping and clear dependency relationships

### 3. Project Management
- **MAINTAIN** a running CHANGELOG.md file
  - Update with every significant change
  - Follow [Keep a Changelog](https://keepachangelog.com/) format
- **MAINTAIN** a running TODO.md list
  - Update immediately when items are completed
  - Add new items as they are discovered
  - Include priority levels and deadlines when known

### 4. Code Excellence Standard
- **ALWAYS AIM** for code and implementations that, in retrospect, are the ONLY solution any expert would arrive at
  - This means choosing the most elegant, efficient, and maintainable approach
  - Avoid clever tricks in favor of clear, obvious solutions
  - The code should feel inevitable, not arbitrary
- **FIX ROOT CAUSES**, not symptoms - conduct additional research to understand fully
- **NO SUBOPTIMAL FALLBACKS** - be confident in chosen strategy and fix it rather than reverting

### 5. Documentation Requirements
- **MAINTAIN** updated documentation for both users and developers
- **ASSUME** later users and developers may be of ANY skill level
  - Include basic setup instructions
  - Provide advanced configuration options
  - Add troubleshooting guides
  - Include code examples for common use cases
- **UPDATE** scripts and documentation for ALL changes, especially when approaches change
  - When libraries/frameworks are replaced due to insufficiency, remove old references from active docs
  - References to deprecated approaches should only remain in changelogs and history documents
  - User guides, APIs, and README files must reflect current/working approaches only
  - Maintain "Last Updated" entries in all documentation files
  - Add changelog summaries to track approach evolution and reasoning

### 6. Performance & Compatibility
- **PRIORITIZE** efficiency in both code execution and application resource usage
  - Profile first, optimize proven bottlenecks - avoid premature optimization
  - Minimize API calls
  - Implement caching where appropriate
  - Use async operations for I/O bound tasks
- **AVOID** using unicode symbols in code and scripts where they will cause logic or visual errors
  - Verify any unicode that is still used will not cause any errors before reporting success

### 7. Safety First Principle
- **INTERACTIONS** with production systems CANNOT break existing functionalities without explicit confirmation
  - Always test in a safe environment first
  - Validate claims before reporting success
  - Provide rollback instructions
  - Document any breaking changes clearly
  - Request explicit user confirmation before implementing breaking changes

### 8. Strategic Problem-Solving Excellence
- **STRATEGIC CONFIDENCE** - commit to optimal solutions and fix them rather than fallback
  - Avoid suboptimal fallbacks - be confident and competent in the chosen strategy
  - Fix the optimal strategy rather than reverting to inferior approaches
  - Challenge suboptimal patterns when encountered
- **ROOT CAUSE ANALYSIS** - solve fundamental problems, not surface symptoms
  - Identify root cause, not symptoms - dig deeper for true understanding
  - Conduct additional research where needed to fully understand problem domains
  - Question assumptions and verify underlying causes before implementing fixes
- **PROFESSIONAL EXCELLENCE STANDARDS** - maintain high standards with transparent communication
  - Do not be a yes-man - provide honest assessments of approaches and trade-offs
  - Present best solution with trade-offs clearly explained
  - Remember user requirements and ask for input before significant changes to strategy

---

## 🔵 CLAUDE CODE PROTECTION (When working in .claude directory)

### Absolute Protection Rules
**NEVER MODIFY** these directories (breaking these = system failure):
- `agents/`, `commands/`, `ide/`, `node_modules/`, `PAT/`, `plugins/`, `projects/`, `statsig/`, `todos/`, `shell-snapshots/`
- Core files: `package.json`, `package-lock.json`, `settings.json`, `.git/`, `.gitignore`

### Safe Modification Zones  
**May modify with proper safeguards**:
- `scripts/`, `docs/`, user-created `.md` files (backup first)

### Mandatory File Organization
**BEFORE creating any documentation**, ensure directories exist:
```bash
mkdir -p docs/{analysis,results,planning,setup,legacy} state backups
```

**File Placement Rules**:
- Analysis documents → `docs/analysis/[DATE]_[TOPIC]_analysis.md`
- Results summaries → `docs/results/[DATE]_[TOPIC]_results.md`  
- State captures → `state/[TIMESTAMP]_project_state.md`
- Planning documents → `docs/planning/[TOPIC]_plan.md`
- Setup guides → `docs/setup/[TOPIC]_setup.md`

**PROHIBITED**: Creating `.md` files in root directory (except CLAUDE.md, README.md)

### Safety Protocol
**Before ANY file operations in .claude directory**:
1. **PATH VALIDATION** - Confirm target is in safe modification zone
2. **BACKUP CREATION** - Git commit or explicit backup  
3. **DEPENDENCY CHECK** - Verify no system references to target
4. **USER CONFIRMATION** - Explicit approval for modifications

---

## 📝 Notes for AI Assistants

When working on any project:
1. Check for project-specific CLAUDE.md or similar documentation
2. Read README.md to understand the project
3. Review recent commits to understand current work
4. Check for TODO.md or issue tracker for pending tasks
5. Ensure all changes align with standing instructions
6. Update documentation immediately after code changes
7. Test thoroughly before committing
8. Ask for clarification if instructions conflict

### Priority Order for Instructions
1. **Project-specific CLAUDE.md** (highest priority)
2. **This general CLAUDE.md** 
3. **Project README and documentation**
4. **Framework/library best practices**
5. **General programming principles** (lowest priority)

Remember: The goal is to create code that is not just functional, but exemplary - the kind of solution that makes other developers say "Of course, that's exactly how it should be done."

---

*Version: 5.0 - Real Perfect - Pre-Bloat Foundation*  
*Based on 2025-08-28 backup with minimal proven additions*  
*Token Count: ~2000 - Maximum productive capacity*