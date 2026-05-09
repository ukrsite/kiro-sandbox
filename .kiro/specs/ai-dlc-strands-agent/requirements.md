# Requirements Document

## Introduction

The AI-DLC Strands Agent is a Python prototype that demonstrates the AWS Strands Agents SDK by implementing the **full AI-Driven Development Life Cycle (AI-DLC) adaptive workflow**. The user provides a **target repository path** (e.g., `kiro-sandbox/services/java-api`) and a **user story** (feature request). The agent analyzes the target repo, asks clarifying questions, walks through the complete AI-DLC Software Development Cycle (SDC), and ultimately modifies the target repo by writing generated code directly into it.

All AI-DLC planning artifacts (requirements, design docs, execution plans, etc.) are written to `{target_repo}/aidlc-docs/`. All generated application code is written directly into the target repo's existing source tree (e.g., `{target_repo}/src/main/java/...`). The agent never writes application code into `aidlc-docs/`.

The agent reads stage-specific rule files from `kiro-sandbox/.kiro/aws-aidlc-rule-details/` to govern each stage's behavior. It tracks workflow state in `{target_repo}/aidlc-docs/aidlc-state.md`, logs all interactions in `{target_repo}/aidlc-docs/audit.md`, and asks clarifying questions using `[Answer]:` tag format in dedicated markdown files before proceeding to each stage.

The service is deployed as a standalone Python CLI application at `ai-dlc-agent/` and uses Amazon Bedrock (Claude) as its underlying model via the Strands Agents SDK. The implementation satisfies all eleven AWS Strands Agents homework requirements: basic agent anatomy, community tools, MCP integration, skills, steering, hooks, interrupts, retries, multi-agent pattern, evaluations, and observability.

## Glossary

- **AI-DLC**: AI-Driven Development Life Cycle — a structured, adaptive software development process with three phases: Inception, Construction, and Operations.
- **Agent**: A Strands `Agent` instance combining a model, system prompt, tools, and optional memory/state.
- **Target_Repo**: The user-specified repository path (e.g., `kiro-sandbox/services/java-api`) that the agent analyzes and modifies. All generated application code is written into this directory; all AI-DLC artifacts are written into `{target_repo}/aidlc-docs/`.
- **Inception_Agent**: The agent responsible for the Inception phase — workspace detection, requirements analysis, user stories, workflow planning, application design, and units generation.
- **Construction_Agent**: The agent responsible for the Construction phase — functional design, NFR requirements, NFR design, infrastructure design, code generation, and build & test.
- **Supervisor_Agent**: The top-level orchestrator that accepts the target repo path and user story, routes execution to the appropriate phase agent, and manages shared workflow state.
- **Skill**: A reusable, composable function decorated with `@tool` that encapsulates a specific capability (e.g., reading rule files, writing artifacts, validating state).
- **Hook**: A callback registered on an agent that fires before or after tool calls to perform cross-cutting concerns (logging, token counting, saving intermediate results).
- **Interrupt**: A human-in-the-loop pause point where the agent suspends execution and waits for explicit user approval before continuing to the next stage.
- **Steering**: System-level instructions embedded in an agent's system prompt that constrain behavior, style, and safety boundaries.
- **MCP_Server**: A Model Context Protocol server that exposes tools to agents; the filesystem MCP server is used to read rule files, scan the target repo, and write artifact and code files.
- **Evaluation**: A test case and evaluator pair (using `strands-evals`) that asserts correctness of agent output against expected criteria.
- **Observability**: The collection of structured logs, execution traces, and metrics (tool call counts, retry counts, latency) emitted during agent execution.
- **Phase**: One of the three high-level AI-DLC lifecycle phases (Inception, Construction, Operations).
- **Stage**: An individual workflow activity within a phase (e.g., Workspace Detection, Requirements Analysis, Code Generation).
- **Artifact**: A structured planning document produced by a stage and written to `{target_repo}/aidlc-docs/` (e.g., `requirements.md`, `execution-plan.md`, `unit-of-work.md`). Never contains application source code.
- **aidlc-docs**: The directory created inside the target repo (`{target_repo}/aidlc-docs/`) where all AI-DLC planning artifacts are stored. Application source code is never written here.
- **aidlc-state.md**: The state tracking file at `{target_repo}/aidlc-docs/aidlc-state.md` that records current phase, completed stages, and next stage.
- **audit.md**: The audit trail file at `{target_repo}/aidlc-docs/audit.md` that logs all agent interactions with timestamps.
- **Rule_File**: A markdown file in `kiro-sandbox/.kiro/aws-aidlc-rule-details/` that defines the steps and constraints for a specific AI-DLC stage.
- **Adaptive_Depth**: The mechanism by which the agent adjusts the level of detail in artifacts based on assessed problem complexity (Minimal, Standard, or Comprehensive).
- **Brownfield**: A target repo that already contains existing source code, requiring Reverse Engineering before Requirements Analysis.
- **Greenfield**: A target repo with no existing source code, proceeding directly to Requirements Analysis.
- **Unit_of_Work**: A logical grouping of user stories for development purposes; the decomposition unit used in the Construction phase.
- **Retry**: Automatic re-execution of a tool call or agent step when the output is malformed, invalid, or fails a quality check.

---

## Requirements

### Requirement 1: Basic Agent Anatomy

**User Story:** As a developer evaluating the Strands SDK, I want each agent to have a clearly defined model, system prompt, tools, and state, so that I can understand the fundamental building blocks of a Strands agent.

#### Acceptance Criteria

1. THE Inception_Agent SHALL be initialized with an Amazon Bedrock Claude model, a system prompt loaded from the inception rule files in `kiro-sandbox/.kiro/aws-aidlc-rule-details/inception/`, at least two tools, and a shared workflow state dictionary that includes the `target_repo` path.
2. THE Construction_Agent SHALL be initialized with an Amazon Bedrock Claude model, a system prompt loaded from the construction rule files in `kiro-sandbox/.kiro/aws-aidlc-rule-details/construction/`, at least two tools, and a shared workflow state dictionary that includes the `target_repo` path.
3. THE Supervisor_Agent SHALL be initialized with an Amazon Bedrock Claude model, a system prompt describing the full AI-DLC workflow, the Inception_Agent and Construction_Agent as sub-agent tools, and a shared workflow state dictionary.
4. WHEN an agent is invoked, THE Agent SHALL pass the current workflow state dictionary (including `target_repo`) as context alongside the user prompt.
5. WHEN an agent completes a stage, THE Agent SHALL update the shared workflow state dictionary with the stage name, completion status, and output artifact paths relative to `target_repo`.
6. THE Supervisor_Agent SHALL expose the model identifier, system prompt, registered tools, and current workflow state as inspectable attributes for demonstration purposes.

---

### Requirement 2: Tools and Community Tools

**User Story:** As a developer, I want the agents to use at least one community-provided tool from `strands-agents-tools`, so that I can see how ready-made capabilities integrate with custom tools.

#### Acceptance Criteria

1. THE Inception_Agent SHALL use at least one tool from the `strands-agents-tools` package (e.g., `file_read`) to read rule files and existing workspace artifacts.
2. THE Construction_Agent SHALL use at least one tool from the `strands-agents-tools` package to read design artifacts and existing source files.
3. WHEN a community tool is invoked, THE Agent SHALL pass only validated, sanitized arguments to the tool.
4. IF a community tool returns an error response, THEN THE Agent SHALL log the error and trigger the retry mechanism defined in Requirement 8.

---

### Requirement 3: MCP Integration

**User Story:** As a developer, I want the agent to connect to a filesystem MCP server, so that I can see how MCP servers extend agent capabilities with external tool providers.

#### Acceptance Criteria

1. THE Inception_Agent SHALL connect to a local filesystem MCP server at startup, scoped to the target repo path, and register its tools for use during the session.
2. WHEN the Inception_Agent reads a rule file from `kiro-sandbox/.kiro/aws-aidlc-rule-details/`, THE Inception_Agent SHALL use the filesystem MCP server's read tool.
3. WHEN the Inception_Agent scans the target repo for existing source files during Workspace Detection, THE Inception_Agent SHALL use the filesystem MCP server's directory listing and read tools.
4. WHEN the Construction_Agent writes a generated artifact to `{target_repo}/aidlc-docs/`, THE Construction_Agent SHALL use the filesystem MCP server's write tool and trigger the interrupt defined in Requirement 7 before writing.
5. WHEN the Construction_Agent writes generated application code to the target repo's source tree (e.g., `{target_repo}/src/`), THE Construction_Agent SHALL use the filesystem MCP server's write tool and trigger the interrupt defined in Requirement 7 before writing.
6. IF the MCP server is unavailable at startup, THEN THE Supervisor_Agent SHALL log a warning and continue execution using fallback direct file I/O tools from `strands-agents-tools`.
7. THE Supervisor_Agent SHALL close the MCP server connection cleanly when the workflow completes or terminates with an error.

---

### Requirement 4: Skills

**User Story:** As a developer, I want the agents to use reusable skill functions, so that I can see how Strands skills encapsulate and compose domain-specific capabilities.

#### Acceptance Criteria

1. THE Inception_Agent SHALL use a skill named `load_rule_file` that accepts a stage name and returns the full text content of the corresponding rule file from `kiro-sandbox/.kiro/aws-aidlc-rule-details/`.
2. THE Construction_Agent SHALL use a skill named `write_aidlc_artifact` that accepts a relative artifact path and content string, writes the planning document to `{target_repo}/aidlc-docs/{relative_path}`, and returns the absolute path written. This skill MUST NOT be used to write application source code.
3. THE Construction_Agent SHALL use a skill named `write_source_file` that accepts a relative source path and content string, writes the file to `{target_repo}/{relative_path}` (outside `aidlc-docs/`), and returns the absolute path written. This skill is used exclusively for generated application code.
4. THE Supervisor_Agent SHALL use a skill named `update_workflow_state` that accepts a stage name and status string, updates `{target_repo}/aidlc-docs/aidlc-state.md`, and appends a timestamped entry to `{target_repo}/aidlc-docs/audit.md`.
5. WHEN the `load_rule_file` skill is called with an unknown stage name, THE Inception_Agent SHALL raise a `SkillOutputError` with a descriptive message naming the missing rule file.
6. WHEN the `write_aidlc_artifact` skill produces output, THE Construction_Agent SHALL validate that the file was written successfully before proceeding to the next stage.
7. THE `load_rule_file` skill SHALL be implemented as a standalone `@tool`-decorated function importable from `app/skills/load_rule_file.py`.
8. THE `write_aidlc_artifact` skill SHALL be implemented as a standalone `@tool`-decorated function importable from `app/skills/write_aidlc_artifact.py`.
9. THE `write_source_file` skill SHALL be implemented as a standalone `@tool`-decorated function importable from `app/skills/write_source_file.py`.
10. THE `update_workflow_state` skill SHALL be implemented as a standalone `@tool`-decorated function importable from `app/skills/update_workflow_state.py`.

---

### Requirement 5: Steering

**User Story:** As a developer, I want each agent to have steering instructions in its system prompt, so that I can see how behavioral constraints and safety boundaries are enforced at the prompt level.

#### Acceptance Criteria

1. THE Inception_Agent's system prompt SHALL instruct the agent to respond only in the context of software development lifecycle activities and refuse off-topic requests with a polite explanation.
2. THE Construction_Agent's system prompt SHALL instruct the agent to produce only technology-agnostic design artifacts and avoid prescribing specific implementation frameworks unless the user explicitly requests them.
3. THE Inception_Agent's system prompt SHALL instruct the agent to always ask clarifying questions using `[Answer]:` tag format in a dedicated markdown file when the user's request is ambiguous, and to wait for answers before proceeding.
4. THE Construction_Agent's system prompt SHALL instruct the agent that generated application code MUST be written to the target repo's source tree (e.g., `{target_repo}/src/`) using the `write_source_file` skill — never into `aidlc-docs/`.
5. THE Construction_Agent's system prompt SHALL instruct the agent that planning artifacts (design docs, execution plans, etc.) MUST be written to `{target_repo}/aidlc-docs/` using the `write_aidlc_artifact` skill — never to the source tree.
6. THE Supervisor_Agent's system prompt SHALL instruct the agent to always check `{target_repo}/aidlc-docs/aidlc-state.md` before starting a new stage, and to resume from the last incomplete stage rather than restarting from the beginning.
7. WHEN an agent receives a request that violates its steering constraints, THE Agent SHALL respond with a polite refusal message and explain which constraint was triggered.

---

### Requirement 6: Hooks

**User Story:** As a developer, I want hooks to fire before and after every tool call, so that I can observe cross-cutting concerns like logging, token counting, and intermediate result persistence.

#### Acceptance Criteria

1. THE Supervisor_Agent SHALL register a `before_tool_call` hook on every agent that logs the tool name, input arguments, and a UTC timestamp to a structured log file.
2. THE Supervisor_Agent SHALL register an `after_tool_call` hook on every agent that logs the tool name, output summary, execution duration in milliseconds, and a UTC timestamp to the same structured log file.
3. THE Supervisor_Agent SHALL register a token-counting hook that increments a session-level counter for input tokens and output tokens after each model invocation.
4. WHEN a stage completes, THE Supervisor_Agent SHALL invoke a hook that serializes the current workflow state dictionary to `outputs/session_state.json` as an intermediate checkpoint.
5. THE hook implementations SHALL be importable from `app/hooks/logging_hook.py` (tool call logging) and `app/hooks/token_hook.py` (token counting).

---

### Requirement 7: Interrupts

**User Story:** As a developer, I want the agent to pause and request human approval before writing any file to disk and before proceeding to each new AI-DLC stage, so that I can see how human-in-the-loop interruption works in a Strands workflow.

#### Acceptance Criteria

1. WHEN the Construction_Agent is about to write any file (artifact or source code) to the target repo, THE Construction_Agent SHALL suspend execution and display the file content, target path, and file type (artifact vs. source code) to the user.
2. WHILE the Construction_Agent is suspended awaiting approval, THE Construction_Agent SHALL accept only "approve" or "reject" as valid user responses.
3. WHEN the user responds "approve", THE Construction_Agent SHALL resume execution and write the file using the appropriate MCP filesystem write tool.
4. WHEN the user responds "reject", THE Construction_Agent SHALL discard the file, log the rejection with a UTC timestamp, and prompt the user for revised instructions.
5. IF the user provides no response within 60 seconds, THEN THE Construction_Agent SHALL treat the interrupt as rejected and log a timeout event.
6. WHEN the Supervisor_Agent completes a stage and is about to proceed to the next stage, THE Supervisor_Agent SHALL present a stage completion summary and wait for explicit user approval before invoking the next stage agent.

---

### Requirement 8: Retries

**User Story:** As a developer, I want the agents to automatically retry failed or low-quality operations, so that I can see how Strands handles transient failures and output validation loops.

#### Acceptance Criteria

1. WHEN a tool call raises an exception, THE Agent SHALL retry the tool call up to three times with exponential backoff starting at one second before propagating the error.
2. WHEN the `load_rule_file` skill returns an empty string or a file shorter than 10 characters, THE Inception_Agent SHALL retry the skill invocation up to three times before raising a `SkillOutputError`.
3. WHEN the `write_aidlc_artifact` skill fails to write the file (e.g., permission error, disk full), THE Construction_Agent SHALL retry the skill invocation up to two times before raising a `SkillOutputError`.
4. THE retry logic SHALL log each retry attempt with the attempt number, reason for retry, and UTC timestamp.
5. WHEN all retry attempts are exhausted, THE Agent SHALL raise a structured error containing the operation name, number of attempts, and the last error message.

---

### Requirement 9: Multi-Agent Pattern

**User Story:** As a developer, I want the service to use the Strands Supervisor multi-agent pattern, so that I can see how a top-level orchestrator delegates work to specialized sub-agents across the Inception and Construction phases.

#### Acceptance Criteria

1. THE Supervisor_Agent SHALL implement the Strands Supervisor (agents-as-tools) pattern, registering Inception_Agent and Construction_Agent as callable tools.
2. WHEN the Supervisor_Agent determines the current workflow stage belongs to the Inception phase, THE Supervisor_Agent SHALL delegate execution to Inception_Agent with the relevant stage context and `target_repo` path.
3. WHEN the Supervisor_Agent determines the current workflow stage belongs to the Construction phase, THE Supervisor_Agent SHALL delegate execution to Construction_Agent with the relevant stage context, `target_repo` path, and all Inception artifacts.
4. THE Supervisor_Agent SHALL expose a single `run(target_repo: str, user_story: str) -> dict` entry point that executes the full AI-DLC workflow from Workspace Detection through Build and Test and returns a consolidated result dictionary.
5. WHEN any agent in the workflow raises an unrecoverable error, THE Supervisor_Agent SHALL halt the workflow, log the failure, and return a partial result dictionary containing all artifacts produced up to the point of failure.
6. THE Supervisor_Agent SHALL record the start time, end time, and total duration of each stage's execution in the result dictionary.

---

### Requirement 10: Evaluations

**User Story:** As a developer, I want a suite of evaluation test cases that assert the correctness of agent output, so that I can see how Strands evaluations validate agent behavior across the full AI-DLC workflow.

#### Acceptance Criteria

1. THE Evaluation_Suite SHALL contain at least five test cases covering: a greenfield project description, a brownfield project description, an ambiguous description requiring clarification, a description that violates steering constraints, and a description that triggers the full Inception-through-Construction workflow.
2. WHEN the Evaluation_Suite runs a test case, THE Evaluation_Suite SHALL invoke the full Supervisor_Agent workflow and capture the output.
3. THE Evaluation_Suite SHALL include an evaluator that verifies `aidlc-docs/aidlc-state.md` is created and contains the expected stage completion entries after a successful Inception phase.
4. THE Evaluation_Suite SHALL include an evaluator that verifies `aidlc-docs/audit.md` contains timestamped entries for every stage approval interaction.
5. THE Evaluation_Suite SHALL include an evaluator that verifies the agent correctly requests clarification using `[Answer]:` tags when the input description is ambiguous.
6. WHEN all evaluations complete, THE Evaluation_Suite SHALL print a summary report showing each case name, pass/fail status, score, and failure reason.
7. THE Evaluation_Suite SHALL be executable via `python evals/run_evals.py` and exit with code 0 when all cases pass and code 1 when any case fails.

---

### Requirement 11: Observability

**User Story:** As a developer, I want the service to emit structured logs, execution traces, and metrics, so that I can see how Strands agent activity is made observable in AWS CloudWatch.

#### Acceptance Criteria

1. THE Supervisor_Agent SHALL emit a structured JSON log entry for every agent invocation containing: agent name, stage name, input length in characters, output length in characters, execution duration in milliseconds, and UTC timestamp.
2. THE Supervisor_Agent SHALL emit a structured JSON log entry for every tool call containing: agent name, tool name, input arguments (sanitized), success/failure status, and UTC timestamp.
3. THE Supervisor_Agent SHALL record the following session-level metrics at the end of each workflow run: total tool calls, total retry attempts, total tokens consumed (input + output), total execution duration in milliseconds, and total stages completed.
4. WHEN running on AWS, THE Supervisor_Agent SHALL publish session-level metrics to Amazon CloudWatch under the namespace `AI-DLC/StrandsAgent` using the `boto3` CloudWatch client.
5. THE Supervisor_Agent SHALL write all structured log entries to both stdout and a local file at `outputs/agent_trace.jsonl` in JSON Lines format (relative to the `ai-dlc-agent/` root).
6. THE Supervisor_Agent SHALL capture and log the Strands SDK execution trace for each agent invocation to enable post-hoc debugging.

---

### Requirement 12: Full AI-DLC Inception Phase

**User Story:** As a developer, I want the agent to execute the complete AI-DLC Inception phase stages against the target repo, so that it produces all required planning and architecture artifacts before any code is generated.

#### Acceptance Criteria

1. WHEN the Supervisor_Agent receives a `target_repo` path and user story, THE Inception_Agent SHALL execute Workspace Detection by scanning `{target_repo}` for existing source files and build files, and SHALL create `{target_repo}/aidlc-docs/aidlc-state.md` with the detected project type (Greenfield or Brownfield) and workspace root path.
2. WHEN Workspace Detection identifies a Brownfield workspace, THE Inception_Agent SHALL execute Reverse Engineering by reading existing source files in `{target_repo}` via MCP and producing architecture, component inventory, and technology stack artifacts in `{target_repo}/aidlc-docs/inception/reverse-engineering/`.
3. THE Inception_Agent SHALL always execute Requirements Analysis by loading the `requirements-analysis.md` rule file, generating clarifying questions in `{target_repo}/aidlc-docs/inception/requirements/requirement-verification-questions.md` using `[Answer]:` tags, waiting for user answers, and producing `{target_repo}/aidlc-docs/inception/requirements/requirements.md`.
4. WHEN Workflow Planning determines User Stories are needed, THE Inception_Agent SHALL execute User Stories by producing `{target_repo}/aidlc-docs/inception/user-stories/stories.md` and `personas.md` following INVEST criteria.
5. THE Inception_Agent SHALL always execute Workflow Planning by loading the `workflow-planning.md` rule file, analyzing scope and risk, determining which conditional stages to execute or skip, and producing `{target_repo}/aidlc-docs/inception/plans/execution-plan.md` with a Mermaid workflow visualization.
6. WHEN Workflow Planning determines Application Design is needed, THE Inception_Agent SHALL execute Application Design by producing component definitions, method signatures, and service layer design artifacts in `{target_repo}/aidlc-docs/inception/application-design/`.
7. WHEN Workflow Planning determines Units Generation is needed, THE Inception_Agent SHALL execute Units Generation by producing `{target_repo}/aidlc-docs/inception/application-design/unit-of-work.md`, `unit-of-work-dependency.md`, and `unit-of-work-story-map.md`.
8. WHEN the Inception_Agent completes each stage, THE Inception_Agent SHALL update `{target_repo}/aidlc-docs/aidlc-state.md` with the stage completion status and wait for explicit user approval before proceeding to the next stage.
9. THE Inception_Agent SHALL log every approval prompt and user response with ISO 8601 timestamps in `{target_repo}/aidlc-docs/audit.md`.

---

### Requirement 13: Full AI-DLC Construction Phase

**User Story:** As a developer, I want the agent to execute the complete AI-DLC Construction phase stages per unit of work, so that it produces design artifacts, generates code directly into the target repo, and validates the build before completing the workflow.

#### Acceptance Criteria

1. WHEN the Construction_Agent begins a unit of work, THE Construction_Agent SHALL load the unit definition from `{target_repo}/aidlc-docs/inception/application-design/unit-of-work.md` and the assigned stories from `unit-of-work-story-map.md`.
2. WHEN Workflow Planning determined Functional Design is needed for a unit, THE Construction_Agent SHALL execute Functional Design by loading the `functional-design.md` rule file and producing `business-logic-model.md`, `business-rules.md`, and `domain-entities.md` in `{target_repo}/aidlc-docs/construction/{unit-name}/functional-design/`.
3. WHEN Workflow Planning determined NFR Requirements are needed for a unit, THE Construction_Agent SHALL execute NFR Requirements by loading the `nfr-requirements.md` rule file and producing NFR artifacts in `{target_repo}/aidlc-docs/construction/{unit-name}/nfr-requirements/`.
4. WHEN Workflow Planning determined NFR Design is needed for a unit, THE Construction_Agent SHALL execute NFR Design by loading the `nfr-design.md` rule file and producing NFR design artifacts in `{target_repo}/aidlc-docs/construction/{unit-name}/nfr-design/`.
5. WHEN Workflow Planning determined Infrastructure Design is needed for a unit, THE Construction_Agent SHALL execute Infrastructure Design by loading the `infrastructure-design.md` rule file and producing infrastructure mapping artifacts in `{target_repo}/aidlc-docs/construction/{unit-name}/infrastructure-design/`.
6. THE Construction_Agent SHALL always execute Code Generation for each unit by loading the `code-generation.md` rule file, creating a code generation plan in `{target_repo}/aidlc-docs/construction/plans/{unit-name}-code-generation-plan.md`, waiting for user approval of the plan, and then writing generated code directly into `{target_repo}`'s existing source tree (e.g., `{target_repo}/src/main/java/`) using the `write_source_file` skill — never into `aidlc-docs/`.
7. THE Construction_Agent SHALL always execute Build and Test by loading the `build-and-test.md` rule file and producing build instructions, unit test instructions, integration test instructions, and a build-and-test summary in `{target_repo}/aidlc-docs/construction/build-and-test/`.
8. WHEN the Construction_Agent completes each stage, THE Construction_Agent SHALL update `{target_repo}/aidlc-docs/aidlc-state.md` with the stage completion status and wait for explicit user approval before proceeding to the next stage.
9. THE Construction_Agent SHALL log every approval prompt and user response with ISO 8601 timestamps in `{target_repo}/aidlc-docs/audit.md`.

---

### Requirement 14: Adaptive Depth and State Resumption

**User Story:** As a developer, I want the agent to adapt its level of detail to problem complexity and resume from the last incomplete stage if interrupted, so that the workflow is efficient and resilient.

#### Acceptance Criteria

1. WHEN the Inception_Agent assesses a user request as Trivial or Simple complexity, THE Inception_Agent SHALL use Minimal depth for Requirements Analysis, producing a concise requirements document without exhaustive clarifying questions.
2. WHEN the Inception_Agent assesses a user request as Moderate complexity, THE Inception_Agent SHALL use Standard depth for Requirements Analysis, producing a full requirements document with functional and non-functional requirements.
3. WHEN the Inception_Agent assesses a user request as Complex, THE Inception_Agent SHALL use Comprehensive depth for Requirements Analysis, producing a detailed requirements document with traceability, risk assessment, and stakeholder analysis.
4. WHEN the Supervisor_Agent starts and `{target_repo}/aidlc-docs/aidlc-state.md` already exists, THE Supervisor_Agent SHALL read the state file, identify the last incomplete stage, and resume execution from that stage rather than restarting from Workspace Detection.
5. WHEN the Supervisor_Agent resumes from a previous session, THE Supervisor_Agent SHALL load all previously generated artifacts from `{target_repo}/aidlc-docs/` before invoking the next stage agent.

---

### Requirement 15: Project Structure and Packaging

**User Story:** As a developer, I want the service to follow the homework assignment's project structure and be self-contained, so that it is easy to set up and consistent with the reference layout.

#### Acceptance Criteria

1. THE Service SHALL be located at `ai-dlc-agent/` and follow this directory structure:

```
ai-dlc-agent/
├── README.md
├── requirements.txt
├── Dockerfile
├── app/
│   ├── main.py                        # CLI: --repo <path> --story <text>
│   ├── workflow.py                    # Supervisor orchestrator
│   ├── agents/
│   │   ├── inception_agent.py
│   │   ├── construction_agent.py
│   │   └── supervisor_agent.py
│   ├── skills/
│   │   ├── load_rule_file.py          # reads kiro-sandbox/.kiro/aws-aidlc-rule-details/
│   │   ├── write_aidlc_artifact.py    # writes to {target_repo}/aidlc-docs/
│   │   ├── write_source_file.py       # writes to {target_repo}/src/ (application code)
│   │   └── update_workflow_state.py   # updates aidlc-state.md and audit.md
│   ├── hooks/
│   │   ├── logging_hook.py
│   │   └── token_hook.py
│   └── observability/
│       ├── logger.py
│       └── metrics.py
├── data/
│   └── dlc_activities.json
├── evals/
│   ├── cases.json
│   └── run_evals.py
├── outputs/
│   └── .gitkeep
└── screenshots/
    └── .gitkeep
```

2. THE CLI entry point SHALL accept `--repo <target_repo_path>` and `--story <user_story_text>` as required arguments, so the user can invoke the agent as: `python -m app.main --repo kiro-sandbox/services/java-api --story "As a user, I want to..."`.
3. THE Service SHALL declare all runtime dependencies in `requirements.txt` including pinned versions of `strands-agents`, `strands-agents-tools`, `strands-evals`, `boto3`, `mcp`, `hypothesis`, `pytest`, and `pytest-mock`.
4. THE Service SHALL include a `README.md` with setup instructions, required AWS environment variables, and commands to run the service and evaluations.
5. THE Service SHALL include a `Dockerfile` at `ai-dlc-agent/Dockerfile` that builds a runnable container image using a Python 3.12 base image.
6. WHEN the service starts, THE Service SHALL validate that required environment variables (`AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` or an IAM role) are present and raise a descriptive `ConfigurationError` if any are missing.
7. THE `outputs/` directory SHALL be git-ignored and used exclusively for generated session state checkpoints and trace logs at runtime.
8. THE `{target_repo}/aidlc-docs/` directory SHALL be created by the agent at runtime and SHALL contain only AI-DLC planning artifact files — never application source code.
