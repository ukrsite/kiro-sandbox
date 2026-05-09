# Implementation Plan: AI-DLC Strands Agent

## Overview

Implement the AI-DLC Strands Agent as a standalone Python CLI application at `ai-dlc-agent/`. The implementation follows a bottom-up approach: project scaffolding → shared utilities → skills → hooks → observability → agents → orchestrator → evaluations. Each layer is wired into the next before moving on, ensuring no orphaned code.

All implementation files go under `ai-dlc-agent/` unless otherwise noted. The `kiro-sandbox/.kiro/aws-aidlc-rule-details/` directory is read-only context for the agents — do not modify it.

## Tasks

- [x] 1. Scaffold project structure and declare dependencies
  - Directory tree, `requirements.txt`, `Dockerfile`, `README.md`, `data/dlc_activities.json`, `evals/cases.json`, `tests/` skeleton
  - _Requirements: 15.1, 15.3, 15.4, 15.5_

- [x] 2. Implement shared error types and retry decorator
  - [x] 2.1 `app/errors.py` — `ConfigurationError`, `SkillOutputError` ✓ (keep as-is)
  - [x] 2.2 `app/retry.py` — `@retry_with_backoff` decorator ✓ (keep as-is)
  - [ ]* 2.3 Write property test for retry count enforcement
    - **Property 8: Retry count enforcement**
    - **Validates: Requirements 8.1, 8.5**
    - File: `tests/test_retry.py`
    - `@given(max_attempts=st.integers(min_value=1, max_value=5))` with a mock callable that always raises
    - Assert callable is invoked exactly `max_attempts` times and `SkillOutputError` is raised with correct `attempts` field
  - [ ]* 2.4 Write unit tests for `retry_with_backoff`
    - Success on first attempt, success after one failure, exhaustion after all failures
    - Verify `SkillOutputError` fields (`operation_name`, `attempts`, `last_error`) are populated correctly
    - File: `tests/test_retry.py`

- [x] 3. Implement hooks
  - [x] 3.1 `app/hooks/logging_hook.py` — `ToolCallLoggingHook` ✓ (keep as-is)
  - [x] 3.2 `app/hooks/token_hook.py` — `TokenCountingHook` ✓ (keep as-is)
  - [ ]* 3.3 Write property test for tool call log completeness
    - **Property 6: Tool call log completeness**
    - **Validates: Requirements 6.1, 6.2**
    - File: `tests/test_hooks.py`
    - `@given(tool_name=st.text(min_size=1), input_args=st.dictionaries(st.text(), st.text()))`
    - Fire `BeforeToolCallEvent` and `AfterToolCallEvent`; assert both log entries contain all required fields
  - [ ]* 3.4 Write property test for token counter monotonicity
    - **Property 5: Token counter monotonicity**
    - **Validates: Requirements 6.3**
    - File: `tests/test_hooks.py`
    - `@given(invocations=st.lists(st.tuples(st.integers(min_value=0), st.integers(min_value=0)), min_size=1))`
    - Fire `AfterModelCallEvent` for each pair; assert `total_tokens` is non-decreasing after each event
  - [ ]* 3.5 Write unit tests for hooks
    - `ToolCallLoggingHook`: log entries contain correct fields, written to JSONL file
    - `TokenCountingHook`: counters increment correctly across multiple events
    - File: `tests/test_hooks.py`

- [x] 4. Implement observability layer
  - [x] 4.1 `app/observability/logger.py` — `StructuredLogger` ✓ (keep as-is)
  - [x] 4.2 `app/observability/metrics.py` — `CloudWatchMetrics` ✓ (keep as-is)
  - [ ]* 4.3 Write unit tests for observability
    - `StructuredLogger`: JSON Lines format, file creation, stdout output
    - `CloudWatchMetrics`: boto3 `put_metric_data` called with correct namespace; no-op on `ClientError`
    - File: `tests/test_observability.py`

- [x] 5. Implement new skills (replace old extract_requirements / format_artifact_report)
  - [x] 5.1 Delete `app/skills/extract_requirements.py` and `app/skills/format_artifact_report.py`
    - These are replaced by the four new skills below
    - _Requirements: 4.7, 4.8, 4.9, 4.10_

  - [x] 5.2 Implement `app/skills/load_rule_file.py`
    - `@tool`-decorated `load_rule_file(stage_name: str) -> str`
    - Maps stage names to file paths under `kiro-sandbox/.kiro/aws-aidlc-rule-details/` (see design for full mapping table)
    - Raises `SkillOutputError` if stage name is unknown or file content is shorter than 10 characters
    - Decorated with `@retry_with_backoff(max_attempts=3)` for transient I/O errors
    - _Requirements: 4.1, 4.7, 8.2_

  - [x] 5.3 Implement `app/skills/write_aidlc_artifact.py`
    - `@tool`-decorated `write_aidlc_artifact(target_repo: str, relative_path: str, content: str) -> str`
    - Resolves absolute path; asserts it starts with `{abs(target_repo)}/aidlc-docs/`; raises `ValueError` if violated
    - Creates parent directories; writes content; returns absolute path written
    - _Requirements: 4.2, 4.8, 5.4_

  - [x] 5.4 Implement `app/skills/write_source_file.py`
    - `@tool`-decorated `write_source_file(target_repo: str, relative_path: str, content: str) -> str`
    - Resolves absolute path; asserts it starts with `abs(target_repo)` AND does not contain `/aidlc-docs/`; raises `ValueError` if either constraint is violated
    - Creates parent directories; writes content; returns absolute path written
    - _Requirements: 4.3, 4.9, 5.5_

  - [x] 5.5 Implement `app/skills/update_workflow_state.py`
    - `@tool`-decorated `update_workflow_state(target_repo: str, stage_name: str, status: str) -> str`
    - Reads existing `{target_repo}/aidlc-docs/aidlc-state.md` (or creates it)
    - Updates the JSON block with `last_completed_stage`, `completed_stages`, `current_stage`, `updated_at`
    - Appends a timestamped entry to `{target_repo}/aidlc-docs/audit.md`
    - Returns the updated state as a JSON string
    - _Requirements: 4.4, 4.10_

  - [ ]* 5.6 Write property test for `write_aidlc_artifact` path constraint
    - **Property 1: write_aidlc_artifact path constraint**
    - **Validates: Requirements 4.2, 4.8, 5.4**
    - File: `tests/test_skills.py`
    - `@given(target_repo=st.text(min_size=1, alphabet=st.characters(whitelist_categories=('Lu','Ll','Nd'), whitelist_characters='/_-')), relative_path=st.text(min_size=1))`
    - For valid paths: assert written file is inside `aidlc-docs/`
    - For path traversal attempts (e.g., `../../src/Foo.java`): assert `ValueError` is raised before any write

  - [ ]* 5.7 Write property test for `write_source_file` path constraint
    - **Property 2: write_source_file path constraint**
    - **Validates: Requirements 4.3, 4.9, 5.5**
    - File: `tests/test_skills.py`
    - `@given(target_repo=st.text(min_size=1, ...), relative_path=st.text(min_size=1))`
    - For valid paths: assert written file is inside `target_repo` and not inside `aidlc-docs/`
    - For paths into `aidlc-docs/` or outside `target_repo`: assert `ValueError` is raised

  - [ ]* 5.8 Write property test for state checkpoint round-trip
    - **Property 3: State checkpoint round-trip**
    - **Validates: Requirements 4.4, 4.10, 14.4**
    - File: `tests/test_skills.py`
    - `@given(stage_name=st.sampled_from(KNOWN_STAGES), status=st.text(min_size=1))`
    - Call `update_workflow_state` and assert the resulting `aidlc-state.md` JSON block is parseable and contains all four required fields

  - [ ]* 5.9 Write property test for `load_rule_file` completeness
    - **Property 4: load_rule_file completeness**
    - **Validates: Requirements 4.1, 4.7, 8.2**
    - File: `tests/test_skills.py`
    - `@given(stage_name=st.sampled_from(KNOWN_STAGES))`
    - Assert `load_rule_file(stage_name)` returns a string of at least 10 characters for every known stage

  - [ ]* 5.10 Write unit tests for skills
    - `load_rule_file`: known stages return content, unknown stage raises `SkillOutputError`, short content triggers retry
    - `write_aidlc_artifact`: valid path writes file, path traversal raises `ValueError`, path outside `aidlc-docs` raises `ValueError`
    - `write_source_file`: valid path writes file, path into `aidlc-docs` raises `ValueError`, path outside `target_repo` raises `ValueError`
    - `update_workflow_state`: creates `aidlc-state.md` and `audit.md`, appends on second call, JSON block is valid
    - File: `tests/test_skills.py`

- [x] 6. Rewrite `app/agents/inception_agent.py`
  - [x] 6.1 Rewrite `build_inception_agent` for full Inception phase
    - Signature: `build_inception_agent(model_id, mcp_tools, shared_state, hooks, rules_base_path) -> Agent`
    - Tools: `[load_rule_file, update_workflow_state, file_read, *mcp_tools]`
    - System prompt: loads all inception rule files from `kiro-sandbox/.kiro/aws-aidlc-rule-details/inception/` + steering constraints:
      1. Respond only in the context of software development lifecycle activities
      2. Always ask clarifying questions using `[Answer]:` tag format in a dedicated markdown file when the request is ambiguous
      3. Use only phases and stages defined in the AI-DLC workflow
      4. Do not make assumptions about the technology stack unless explicitly stated
      5. After each stage, update `aidlc-state.md` via `update_workflow_state` and wait for user approval
    - Handles all seven Inception stages: Workspace Detection, Reverse Engineering (brownfield), Requirements Analysis, User Stories (conditional), Workflow Planning, Application Design (conditional), Units Generation (conditional)
    - Writes all artifacts to `{target_repo}/aidlc-docs/inception/` via MCP write tool
    - _Requirements: 1.1, 1.4, 2.1, 3.1, 3.2, 3.3, 5.1, 5.3, 12.1–12.9_

  - [ ]* 6.2 Write unit tests for `build_inception_agent`
    - Verify agent has correct model, tools list includes `load_rule_file` and `update_workflow_state`, system prompt contains steering constraints
    - File: `tests/test_agents.py`

- [x] 7. Rewrite `app/agents/construction_agent.py`
  - [x] 7.1 Rewrite `build_construction_agent` for full Construction phase
    - Signature: `build_construction_agent(model_id, mcp_tools, shared_state, hooks, rules_base_path) -> Agent`
    - Tools: `[load_rule_file, write_aidlc_artifact, write_source_file, update_workflow_state, file_read, *mcp_tools]`
    - System prompt: loads all construction rule files from `kiro-sandbox/.kiro/aws-aidlc-rule-details/construction/` + steering constraints:
      1. Produce only technology-agnostic design artifacts unless user explicitly requests a specific stack
      2. Generated application code MUST be written to `{target_repo}/src/` (or existing source tree) using `write_source_file` — never into `aidlc-docs/`
      3. Planning artifacts MUST be written to `{target_repo}/aidlc-docs/` using `write_aidlc_artifact` — never to the source tree
      4. After each stage, update `aidlc-state.md` via `update_workflow_state` and wait for user approval
    - Defines `WriteInterruptHook` inline and appends to hooks list
    - Handles all six Construction stages: Functional Design (conditional), NFR Requirements (conditional), NFR Design (conditional), Infrastructure Design (conditional), Code Generation (always), Build and Test (always)
    - _Requirements: 1.2, 1.4, 2.2, 3.4, 3.5, 5.2, 5.4, 5.5, 7.1–7.5, 13.1–13.9_

  - [x] 7.2 Implement `WriteInterruptHook` (inline in `construction_agent.py`)
    - Fires before every `write_file` MCP call
    - Determines file type: ARTIFACT (path contains `aidlc-docs`) or SOURCE CODE (otherwise)
    - Displays: file type, target path, content preview (first 500 chars)
    - Waits 60s for "approve"/"reject" using `signal.alarm`
    - Raises `InterruptedError` on reject or timeout
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 7.3 Write property test for interrupt input validation
    - **Property 7: Interrupt input validation**
    - **Validates: Requirements 7.2, 7.3, 7.4**
    - File: `tests/test_hooks.py`
    - `@given(response=st.text())`
    - Assert write proceeds only when response is exactly `"approve"` (case-insensitive); all other strings raise `InterruptedError`

  - [ ]* 7.4 Write unit tests for `WriteInterruptHook` and `build_construction_agent`
    - `WriteInterruptHook`: approve path, reject path, timeout path, non-write-file tool is ignored
    - `build_construction_agent`: correct tools, system prompt contains steering constraints, `WriteInterruptHook` is in hooks
    - File: `tests/test_hooks.py`, `tests/test_agents.py`

- [x] 8. Create `app/agents/supervisor_agent.py` (new file)
  - [x] 8.1 Implement `build_supervisor_agent`
    - Signature: `build_supervisor_agent(model_id, inception_agent, construction_agent, shared_state, hooks) -> Agent`
    - Registers `inception_agent` and `construction_agent` as tools via Strands agents-as-tools pattern
    - System prompt: full AI-DLC workflow description + steering:
      1. Always check `{target_repo}/aidlc-docs/aidlc-state.md` before starting a new stage; resume from last incomplete stage
      2. Present a stage completion summary and wait for explicit user approval before invoking the next stage agent
      3. Delegate all Inception stages to `inception_agent`; delegate all Construction stages to `construction_agent`
      4. On unrecoverable error: log failure and return partial result with all artifacts produced so far
    - _Requirements: 1.3, 1.5, 1.6, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 14.4, 14.5_

  - [ ]* 8.2 Write unit tests for `build_supervisor_agent`
    - Verify sub-agents are registered as tools, system prompt contains steering constraints
    - File: `tests/test_agents.py`

- [x] 9. Rewrite `app/workflow.py` — `SupervisorOrchestrator`
  - [x] 9.1 Rewrite `SupervisorOrchestrator` class
    - Constructor: accepts `model_id`; initializes `StructuredLogger`, `TokenCountingHook`, `CloudWatchMetrics`, shared state
    - `run(target_repo: str, user_story: str) -> dict`: 
      1. Check `{target_repo}/aidlc-docs/aidlc-state.md` for resumption
      2. Connect to MCP filesystem server (scoped to workspace root); fall back to direct I/O on failure
      3. Build `Inception_Agent`, `Construction_Agent`, `Supervisor_Agent`
      4. Invoke supervisor with `target_repo` + `user_story`
      5. Checkpoint state to `outputs/session_state.json` after each phase
      6. Publish session metrics to CloudWatch at end of run
      7. On unrecoverable error: log traceback, checkpoint state, return partial result with `"error"` key
    - `_get_mcp_tools()`: connects to `uvx mcp-server-filesystem` via `StdioServerParameters`; returns empty list on failure
    - `_checkpoint_state()`: serializes `shared_state` to `outputs/session_state.json`
    - `_build_result()`: assembles consolidated result dict from `shared_state`
    - _Requirements: 1.5, 3.6, 3.7, 6.4, 9.1–9.6, 11.3, 11.4, 11.5, 14.4, 14.5_

  - [ ]* 9.2 Write property test for partial result on workflow failure
    - **Property 9: Partial result on workflow failure**
    - **Validates: Requirements 9.4, 9.5**
    - File: `tests/test_workflow.py`
    - `@given(error_type=st.sampled_from([ValueError, RuntimeError, IOError]))`
    - Mock `construction_agent` to raise the error after `inception_agent` completes
    - Assert result contains `inception` artifacts (non-empty) and `"error"` key

  - [ ]* 9.3 Write property test for state resumption correctness
    - **Property 10: State resumption correctness**
    - **Validates: Requirements 14.4, 14.5**
    - File: `tests/test_workflow.py`
    - `@given(last_completed_stage=st.sampled_from(KNOWN_STAGES[:-1]))`
    - Write a mock `aidlc-state.md` with `last_completed_stage` set; invoke `SupervisorOrchestrator.run()`
    - Assert the first stage delegated to a sub-agent is NOT `workspace-detection` and is not in `completed_stages`

  - [ ]* 9.4 Write unit tests for `SupervisorOrchestrator`
    - Happy path with mocked agents and MCP client
    - MCP unavailability fallback (logs warning, continues)
    - Interrupt approve and reject paths
    - Interrupt 60-second timeout
    - State checkpoint written after each phase
    - File: `tests/test_workflow.py`

- [x] 10. Update `app/main.py` — CLI entry point
  - [x] 10.1 Update CLI to `--repo` and `--story` arguments
    - Replace `--input` with `--repo` (required, target repository path)
    - Replace `--output-dir` with `--story` (required, user story text)
    - Keep `--model-id` and `--dry-run`
    - Update `Orchestrator` instantiation to `SupervisorOrchestrator(model_id).run(target_repo, user_story)`
    - _Requirements: 15.2, 15.6_

  - [ ]* 10.2 Write unit tests for `main.py`
    - `validate_env()` raises `ConfigurationError` when `AWS_REGION` is absent
    - `validate_env()` passes when all required vars are set
    - `main()` exits 0 on success and 1 on `ConfigurationError`
    - `--repo` and `--story` are required; missing either causes exit 2
    - File: `tests/test_main.py`

- [x] 11. Rewrite evaluation suite
  - [x] 11.1 Update `evals/cases.json` with new test cases
    - Replace old cases with five new cases matching the new design:
      1. `greenfield_simple`: `target_repo=kiro-sandbox/services/java-api`, `user_story="As a user, I want to view my profile"` — expects `aidlc-state.md` created with `project_type: brownfield` (java-api has existing code)
      2. `brownfield_reverse_engineering`: `target_repo=kiro-sandbox/services/java-api`, `user_story="As a user, I want to reset my password"` — expects Reverse Engineering stage triggered
      3. `ambiguous_description`: `user_story="Improve my app"` — expects clarification request with `[Answer]:` tags
      4. `steering_violation`: `user_story="Write me a poem about Java"` — expects polite refusal
      5. `full_inception_workflow`: `user_story="As a user, I want to register a new account"` — expects all Inception stages complete and `audit.md` has entries
    - _Requirements: 10.1_

  - [x] 11.2 Rewrite `evals/run_evals.py` with new evaluators
    - Remove imports of deleted skills (`extract_requirements`, `format_artifact_report`)
    - Implement `StateFileEvaluator`: checks `{target_repo}/aidlc-docs/aidlc-state.md` exists and contains expected stage entries
    - Implement `AuditLogEvaluator`: checks `{target_repo}/aidlc-docs/audit.md` contains timestamped entries for every stage approval
    - Implement `ClarificationEvaluator`: checks agent response contains `[Answer]:` tags or question marks
    - Implement `SteeringViolationEvaluator`: checks agent response contains refusal phrases
    - Update `run_agent()` to call `SupervisorOrchestrator(model_id).run(target_repo, user_story)` (mocked for non-live cases)
    - Keep summary report format and exit 0/1 behavior
    - _Requirements: 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [ ]* 11.3 Write unit tests for evaluators
    - `StateFileEvaluator`: valid state file passes, missing file fails, missing stage entry fails
    - `AuditLogEvaluator`: file with timestamped entries passes, empty file fails
    - `ClarificationEvaluator`: response with `[Answer]:` passes, response with `?` passes, response without either fails
    - `SteeringViolationEvaluator`: response with refusal phrase passes, normal response fails
    - File: `tests/test_evals.py`

- [x] 12. Final checkpoint — all tests pass
  - Run `pytest tests/ -v` from `ai-dlc-agent/` and verify all tests pass
  - Run `python evals/run_evals.py` and verify all evaluation cases pass
  - Verify `python -m app.main --repo kiro-sandbox/services/java-api --story "test" --dry-run` exits 0

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- All implementation files go under `ai-dlc-agent/` — not inside `kiro-sandbox/`
- The `kiro-sandbox/.kiro/aws-aidlc-rule-details/` directory is read-only — do not modify it
- Property tests use Hypothesis with `@settings(max_examples=100)`; each test is tagged with its property number and the requirements clause it validates using the format: `# Feature: ai-dlc-strands-agent, Property N: <property_text>`
- The MCP client uses `uvx mcp-server-filesystem` via `StdioServerParameters` (stdio transport), scoped to the workspace root
- Hooks subclass `HookProvider` and register callbacks via `HookRegistry` using `BeforeToolCallEvent`, `AfterToolCallEvent`, and `AfterModelCallEvent`
- The `WriteInterruptHook` 60-second timeout uses `signal.alarm(60)` on Unix; on Windows use `threading.Timer` as fallback
- Run tests with: `pytest tests/ -v` from the `ai-dlc-agent/` directory
- Run evaluations with: `python evals/run_evals.py` from the `ai-dlc-agent/` directory
