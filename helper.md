# CareerCraft AI – Technical Implementation Blueprint
## Folder Structure, Development Phases and Implementation Guidelines

**Project Name:** CareerCraft AI  
**Project Type:** Multi-Agent AI Job Application Assistant  
**Backend:** Python + FastAPI  
**Frontend:** React + TypeScript  
**Agent Framework:** LangGraph  
**Database:** PostgreSQL  
**Vector Database:** ChromaDB  
**LLM:** Gemini (configurable provider)  
**MCP:** Python MCP SDK  
**Observability:** LangSmith  

---

# PART 1 – PROJECT ARCHITECTURE

## 1. Architectural Approach

Use a modular monolithic architecture.

The application should have:

1. FastAPI backend.
2. React frontend.
3. LangGraph multi-agent orchestration.
4. Separate MCP servers for GitHub and Google Drive.
5. Persistent candidate knowledge base.
6. RAG retrieval system.
7. LaTeX document generation.
8. Independent LLM-as-a-Judge evaluation.
9. ReAct-based revision mechanism.

Do not introduce microservices unnecessarily.

Keep individual responsibilities separated into modules so they can be maintained and tested independently.

## 2. Complete Folder Structure

Create the following target project structure:

```text
careercraft-ai/
│
├── backend/
│   │
│   ├── app/
│   │   │
│   │   ├── agents/
│   │   │   ├── supervisor/
│   │   │   │   ├── agent.py
│   │   │   │   └── prompts.py
│   │   │   │
│   │   │   ├── job_analysis/
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompts.py
│   │   │   │   └── output.py
│   │   │   │
│   │   │   ├── candidate_analysis/
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompts.py
│   │   │   │   └── output.py
│   │   │   │
│   │   │   ├── application_generation/
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompts.py
│   │   │   │   └── output.py
│   │   │   │
│   │   │   ├── revision/
│   │   │   │   ├── agent.py
│   │   │   │   └── prompts.py
│   │   │   │
│   │   │   └── judge/
│   │   │       ├── evaluator.py
│   │   │       ├── prompts.py
│   │   │       └── output.py
│   │   │
│   │   ├── graph/
│   │   │   ├── state.py
│   │   │   ├── workflow.py
│   │   │   ├── nodes.py
│   │   │   ├── routing.py
│   │   │   ├── edges.py
│   │   │   ├── checkpoint.py
│   │   │   └── subgraphs.py
│   │   │
│   │   ├── mcp/
│   │   │   ├── client/
│   │   │   │   ├── github_client.py
│   │   │   │   └── drive_client.py
│   │   │   └── registry.py
│   │   │
│   │   ├── rag/
│   │   │   ├── ingestion/
│   │   │   │   ├── drive_ingestion.py
│   │   │   │   ├── github_ingestion.py
│   │   │   │   └── document_parser.py
│   │   │   │
│   │   │   ├── processing/
│   │   │   │   ├── chunking.py
│   │   │   │   ├── embeddings.py
│   │   │   │   └── metadata.py
│   │   │   │
│   │   │   ├── retrieval/
│   │   │   │   ├── retriever.py
│   │   │   │   ├── filters.py
│   │   │   │   └── ranking.py
│   │   │   │
│   │   │   └── vector_store.py
│   │   │
│   │   ├── memory/
│   │   │   ├── short_term.py
│   │   │   ├── long_term.py
│   │   │   ├── candidate_memory.py
│   │   │   └── synchronization.py
│   │   │
│   │   ├── tools/
│   │   │   ├── jd_tools.py
│   │   │   ├── document_tools.py
│   │   │   └── validation_tools.py
│   │   │
│   │   ├── document_generation/
│   │   │   ├── resume/
│   │   │   │   ├── generator.py
│   │   │   │   └── schema.py
│   │   │   │
│   │   │   ├── cover_letter/
│   │   │   │   ├── generator.py
│   │   │   │   └── schema.py
│   │   │   │
│   │   │   ├── latex/
│   │   │   │   ├── renderer.py
│   │   │   │   ├── validator.py
│   │   │   │   ├── compiler.py
│   │   │   │   └── templates/
│   │   │   │       ├── modern.tex
│   │   │   │       ├── minimal.tex
│   │   │   │       └── technical.tex
│   │   │   │
│   │   │   └── versioning.py
│   │   │
│   │   ├── evaluation/
│   │   │   ├── judge.py
│   │   │   ├── factual_evaluation.py
│   │   │   ├── jd_alignment.py
│   │   │   ├── retrieval_evaluation.py
│   │   │   └── metrics.py
│   │   │
│   │   ├── guardrails/
│   │   │   ├── input_validation.py
│   │   │   ├── output_validation.py
│   │   │   ├── evidence_checker.py
│   │   │   ├── prompt_injection.py
│   │   │   └── permissions.py
│   │   │
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   ├── session.py
│   │   │   └── repositories/
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── dependencies.py
│   │   │
│   │   ├── auth/
│   │   │   ├── jwt.py
│   │   │   ├── oauth.py
│   │   │   └── security.py
│   │   │
│   │   ├── config/
│   │   │   └── settings.py
│   │   │
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── workflow/
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── mcp_servers/
│   │
│   ├── github_mcp/
│   │   ├── server.py
│   │   ├── tools/
│   │   │   ├── repositories.py
│   │   │   ├── files.py
│   │   │   └── commits.py
│   │   └── requirements.txt
│   │
│   └── google_drive_mcp/
│       ├── server.py
│       ├── tools/
│       │   ├── search.py
│       │   ├── documents.py
│       │   └── folders.py
│       └── requirements.txt
│
├── frontend/
│   │
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── contexts/
│   │   ├── types/
│   │   └── App.tsx
│   │
│   ├── public/
│   ├── package.json
│   └── .env.example
│
├── storage/
│   ├── uploads/
│   ├── generated/
│   └── temp/
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

This is the target structure. Create folders and files incrementally during the relevant development phases rather than generating empty files for the entire project upfront.

---

# PART 2 – DEVELOPMENT PHASES

## PHASE 1: Project Foundation and Authentication

**Objective:** Establish the frontend, backend and database foundations.

Tasks:

1. Initialize the React + TypeScript frontend.
2. Initialize the FastAPI backend.
3. Configure PostgreSQL.
4. Configure SQLAlchemy.
5. Implement database connection and session management.
6. Implement user registration.
7. Implement login.
8. Implement JWT authentication.
9. Implement password hashing.
10. Create protected frontend routes.
11. Create the initial dashboard.

Expected result:

A user can register, log in and access a protected dashboard.

Completion criteria:
- Authentication works.
- User records persist in PostgreSQL.
- Passwords are securely hashed.
- Protected API routes reject unauthorized requests.

---

## PHASE 2: Candidate Onboarding and External Connections

**Objective:** Allow users to connect their external accounts and discover candidate information.

Tasks:

1. Implement Google OAuth 2.0.
2. Implement GitHub OAuth.
3. Store external account connections securely.
4. Retrieve authorized Google Drive file metadata.
5. Identify relevant PDF, DOCX and other supported documents.
6. Retrieve authorized GitHub repositories.
7. Identify relevant repository metadata and files.
8. Build the initial candidate information discovery workflow.

Expected result:

The user can connect Google Drive and GitHub, and the application can discover relevant candidate documents and repositories.

Completion criteria:
- Both integrations authenticate successfully.
- External permissions are appropriately restricted.
- Relevant documents and repositories can be discovered.
- The user can review discovered information.

---

## PHASE 3: Candidate Knowledge Base and RAG

**Objective:** Create persistent candidate intelligence.

Tasks:

1. Implement PDF and DOCX extraction.
2. Implement GitHub README and source-file extraction.
3. Implement text preprocessing.
4. Implement document chunking.
5. Generate embeddings.
6. Configure PGVectorStore.
7. Store document and project embeddings.
8. Store structured candidate information in PostgreSQL.
9. Implement candidate profile creation.
10. Implement metadata-based retrieval.
11. Implement semantic retrieval.
12. Implement incremental synchronization.
13. Implement candidate information update and deletion.
14. Optionally create a dedicated Google Drive Candidate Knowledge Base folder.

Expected result:

The candidate's verified information is stored in a persistent hybrid knowledge base.

Completion criteria:
- Candidate information can be retrieved semantically.
- Relevant source references are preserved.
- Different users' data remains isolated.
- Updated documents can be synchronized without reprocessing everything unnecessarily.

---

## PHASE 4: Job Description Ingestion and Analysis

**Objective:** Build the job description processing pipeline.

Tasks:

1. Implement URL input.
2. Implement PDF upload.
3. Implement plain-text input.
4. Extract and normalize JD content.
5. Handle inaccessible URLs and unsupported documents.
6. Define Pydantic schemas for job analysis.
7. Implement the Job Analysis Agent.
8. Extract required skills.
9. Extract preferred skills.
10. Extract responsibilities.
11. Extract educational and experience requirements.
12. Extract important keywords.

Expected result:

The system can accept three JD formats and produce structured job analysis.

Completion criteria:
- All three input methods work.
- Structured outputs are validated.
- Missing or ambiguous information is handled appropriately.

---

## PHASE 5: Multi-Agent Architecture and Supervisor

**Objective:** Implement the central LangGraph orchestration architecture.

Tasks:

1. Learn and implement LangGraph shared state.
2. Define the main application state.
3. Implement the Job Analysis Agent as a graph node or specialist agent.
4. Implement the Candidate Profile Analysis Agent.
5. Implement the Supervisor Agent.
6. Configure parallel execution of Job Analysis and Candidate Analysis.
7. Combine the two agents' outputs.
8. Implement structured inter-agent communication.
9. Implement conditional routing.
10. Implement graph checkpointing.
11. Test the complete workflow using manually supplied candidate information initially.

Expected result:

The Supervisor can delegate work to both specialist agents, collect their results and coordinate the next stage.

Completion criteria:
- Both agents execute independently.
- Parallel execution works.
- Their outputs are combined correctly.
- Shared state updates work.
- Checkpointing persists the workflow.

Important: Do not implement every agent as a separate autonomous ReAct loop. Use deterministic graph nodes and structured LLM calls where appropriate.

---

## PHASE 6: MCP Integration

**Objective:** Give the agents standardized access to external services.

Tasks:

### GitHub MCP Server

Implement tools such as:

- Search repositories.
- Get repository details.
- List repository files.
- Read relevant source files.
- Retrieve README files.
- Retrieve dependency information.
- Retrieve commit metadata where useful.

### Google Drive MCP Server

Implement tools such as:

- Search documents.
- List files.
- Retrieve document metadata.
- Download or retrieve authorized file content.
- Create a dedicated folder when explicitly approved.
- Organize curated copies or references when requested.

### MCP Client Integration

1. Configure the backend MCP client.
2. Connect to the GitHub MCP server.
3. Connect to the Google Drive MCP server.
4. Discover available tools.
5. Register tools for appropriate agents.
6. Implement tool execution and error handling.
7. Test tool permissions and responses.

Expected result:

The Candidate Profile Analysis Agent can retrieve candidate information through MCP-connected services.

Completion criteria:
- MCP servers work independently.
- The backend can discover and invoke their tools.
- External tool failures are handled.
- The agents receive structured tool results.

---

## PHASE 7: Resume and Cover Letter Generation

**Objective:** Generate personalized application content.

Tasks:

1. Define resume Pydantic schemas.
2. Define cover letter Pydantic schemas.
3. Implement the Application Generation Agent.
4. Pass Job Analysis results to the generation agent.
5. Pass Candidate Analysis results to the generation agent.
6. Implement project selection.
7. Implement skill prioritization.
8. Generate professional summaries.
9. Generate tailored resume content.
10. Generate personalized cover letters.
11. Implement evidence-based claim validation.
12. Store generated document versions.

Expected result:

The Application Generation Agent produces structured, job-specific resume and cover letter content.

Completion criteria:
- Outputs follow predefined schemas.
- Candidate facts are preserved.
- Relevant projects are selected.
- Unsupported experience is not invented.

---

## PHASE 8: Human-in-the-Loop, LLM Judge and ReAct Revision

**Objective:** Implement human approval and iterative document evaluation.

### A. Human-in-the-Loop

Tasks:

1. Implement LangGraph interrupt functionality.
2. Configure persistent checkpointing.
3. Pause the workflow for user approval.
4. Display selected candidate information.
5. Allow users to approve or request changes.
6. Resume the workflow using the user's response.

### B. LLM-as-a-Judge

Tasks:

1. Implement an independent evaluator.
2. Define structured evaluation output.
3. Evaluate factual accuracy.
4. Evaluate JD alignment.
5. Evaluate project relevance.
6. Detect unsupported claims.
7. Evaluate grammar and readability.
8. Provide actionable feedback.
9. Return APPROVED or REJECTED.

### C. ReAct Revision Agent

Tasks:

1. Implement the Revision Agent.
2. Follow Reason → Act → Observe.
3. Receive rejection feedback.
4. Revise the relevant documents.
5. Return revised documents to the Judge.
6. Implement conditional routing.
7. Limit automatic revisions to three attempts initially.
8. Escalate unresolved failures to human review.

### D. Additional Guardrails

Implement:
- Input validation.
- Output validation.
- Evidence verification.
- Prompt-injection defenses.
- User-specific data access controls.
- Maximum iteration limits.

Expected result:

The system pauses for human approval, independently evaluates generated documents and automatically improves rejected documents within a bounded revision loop.

Completion criteria:
- HITL pauses and resumes correctly.
- Judge returns structured decisions.
- Revision feedback is applied.
- Approved documents exit the loop.
- Maximum retries are enforced.
- Unresolved failures are escalated.

---

## PHASE 9: LaTeX Generation and Frontend Integration

**Objective:** Generate LaTeX source code and provide document preview and PDF download.

### Backend tasks

1. Implement Jinja2-based LaTeX rendering.
2. Create predefined resume templates.
3. Create cover letter templates.
4. Implement safe LaTeX escaping.
5. Implement LaTeX syntax validation.
6. Preserve generated document versions.
7. Return approved `.tex` source files to the frontend.

### Frontend tasks

1. Build the resume preview interface.
2. Build the cover letter preview interface.
3. Integrate a browser-compatible LaTeX rendering solution.
4. Implement source code editing.
5. Implement LaTeX-to-PDF compilation.
6. Implement resume PDF download.
7. Implement cover letter PDF download.
8. Implement template selection.
9. Implement document version history.

Expected result:

The user receives approved LaTeX source code, can preview and edit documents, and can compile and download PDFs directly within the application.

Important:
- Do not use an LLM to generate arbitrary LaTeX templates on every request.
- Prefer deterministic templates.
- A LaTeX viewer alone is not a compiler. Ensure the frontend solution actually supports compilation.
- If browser-side compilation proves impractical, use a separate secure compilation service as a fallback.
- The backend's final document output remains LaTeX source code, not a generated PDF.

---

## PHASE 10: Testing, Observability and Deployment

**Objective:** Make the application reliable and deployable.

Tasks:

### Testing

1. Unit tests for individual agents.
2. Unit tests for RAG retrieval.
3. Tests for MCP tools.
4. API integration tests.
5. LangGraph workflow tests.
6. HITL interruption and resumption tests.
7. Judge and revision loop tests.
8. LaTeX validation tests.
9. Authentication and authorization tests.
10. Multi-user data isolation tests.

### Observability

Integrate LangSmith to monitor:

- Agent execution.
- LLM calls.
- Tool calls.
- Agent outputs.
- Graph transitions.
- Revision cycles.
- Latency.
- Token usage.
- Errors.

### Deployment

1. Create backend Dockerfile.
2. Configure frontend production build.
3. Configure Docker Compose for local development.
4. Configure environment variables.
5. Configure PostgreSQL persistence.
6. Configure ChromaDB persistence.
7. Deploy backend.
8. Deploy frontend.
9. Configure production OAuth callbacks.
10. Test the complete production workflow.

Expected result:

A deployed application with authentication, persistent storage, multi-agent orchestration, external integrations, document generation and observability.

---

# PART 3 – PHASE COMPLETION RULES

Antigravity must follow these rules throughout development.

## 1. Sequential Implementation

Implement one phase at a time.

Do not begin the next major phase until the current phase is implemented, tested and reviewed.

## 2. Do Not Overbuild

Do not generate the complete application in a single operation.

Do not create unused folders, empty modules or placeholder agents unnecessarily.

Create files only when their functionality is required.

## 3. Preserve Architecture

Follow the agreed responsibilities:

- Supervisor: orchestration.
- Job Analysis: job understanding.
- Candidate Analysis: candidate understanding and evidence retrieval.
- Application Generation: resume and cover letter creation.
- Judge: independent evaluation.
- Revision Agent: ReAct-based correction.

Do not merge all responsibilities into one giant agent.

Do not create additional agents without a clear functional reason.

## 4. Test Before Moving Forward

At the end of every phase:

1. Explain what was implemented.
2. List the important files created or modified.
3. Explain how the functionality works.
4. Provide testing instructions.
5. Execute available tests.
6. Identify known limitations.
7. Ask for approval before proceeding to the next phase.

## 5. Maintain Documentation

Update README.md as the project progresses.

Document:
- Architecture decisions.
- API endpoints.
- Environment variables.
- Database models.
- Agent responsibilities.
- MCP tools.
- RAG pipeline.
- Workflow changes.
- Testing instructions.

## 6. Security Rules

- Never hardcode API keys.
- Never commit `.env`.
- Use secure OAuth token storage.
- Isolate candidate data by authenticated user.
- Treat external documents and repository content as untrusted data.
- Validate tool inputs and outputs.
- Restrict filesystem access during LaTeX compilation.
- Never expose one user's documents to another user.

## 7. Technology Discipline

Use Python and FastAPI for backend development.

Use React and TypeScript for the frontend.

Use LangGraph for orchestration.

Use Pydantic for structured outputs.

Use PostgreSQL for structured application data and workflow persistence.

Use ChromaDB for semantic retrieval.

Use MCP for external tool interoperability.

Use LangSmith for observability.

Use deterministic Python functions for operations that do not require LLM reasoning.

---

# PART 4 – IMPLEMENTATION WORKING PROTOCOL

Before implementing any phase, Antigravity should:

1. Review the current project state.
2. Read the project documentation.
3. Identify dependencies from previous phases.
4. Explain the proposed implementation briefly.
5. Implement only the approved phase.
6. Test the functionality.
7. Update documentation.

Do not assume that a future feature has already been implemented.

Do not silently change the agreed architecture.

If a technical limitation requires an architectural change, explain the problem and propose alternatives before implementing the change.

**The user will approve each phase before development proceeds.**

---

# FINAL PROJECT SUCCESS CRITERIA

CareerCraft AI will be considered functionally complete when:

1. A user can register and authenticate.
2. A user can connect Google Drive and GitHub.
3. Candidate information can be collected and maintained in a hybrid knowledge base.
4. A user can submit a JD using URL, PDF or plain text.
5. The Supervisor can coordinate specialized agents.
6. Job and Candidate Analysis can execute independently and in parallel.
7. Candidate evidence can be retrieved using RAG.
8. GitHub and Drive tools can be accessed through MCP.
9. The Application Generation Agent can create tailored resume and cover letter content.
10. The user can approve candidate information through HITL.
11. The LLM Judge can independently evaluate documents.
12. The ReAct Revision Agent can correct rejected documents.
13. The revision loop has a bounded retry mechanism.
14. Approved documents are rendered into valid LaTeX source.
15. The frontend supports preview, editing and PDF download.
16. The application has automated tests, observability and deployment support.

**Final development principle: Build incrementally, test continuously, maintain architectural discipline, and prioritize a working end-to-end application over unnecessary complexity.**

End of Technical Implementation Blueprint.