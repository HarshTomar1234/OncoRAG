**OncoPilot Multi‑Agent DB Plan – Collection‑Centric Revision**

**Goal** Extend the original MCP & multi‑agent architecture so that every *database collection* is represented by a dedicated specialist agent. A central **Query‑Orchestrator**  decomposes end‑user  questions,  delegates  sub‑tasks  to  these  specialists,  then  aggregates  and summarises the combined evidence.![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.001.png)

1. **Collections, Purpose & Specialist Agents**

Database ![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.002.png)![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.003.png)

Specialist Agent Purpose / Core Responsibility

Collection

Retrieve structured data on cancers and their sub‑types,

associated biomarkers, incidence & prevalence metrics, cancers **CancerAgent**

staging calculators, and links to major clinical guidelines / calculators.

Fetch gene‑centric clinical & scientific metadata: cancer genes **GeneAgent** associations, co‑mutations, prognosis impact, linked drugs &

trials, and regulatory notes about actionable variants.

Access comprehensive cancer‑drug information:

pharmacologic class, biomarker relevance, global approvals, drugs **DrugAgent**

efficacy summaries, multi‑geography trial data, and links to regulatory / clinical guidelines.

Provide detailed data on cancer drugs available in India:

CDSCO approval status, biomarkers, cancer indications, local drugs\_india **DrugIndiaAgent**

pricing/availability, supporting evidence from Indian & global sources.

Each specialist knows *only* the schema & business logic of its home collection and owns a tight set of MCP ![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.004.png)![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.005.png)**tools** (e.g.  cancers.search\_cancer ,  genes.get\_gene\_variants ).![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.006.png)

2. **Query‑Orchestrator Agent**
- **Context window** is primed with capsule schema docs for *all* four collections so it grasps their data vocabulary.
- Implements a *ReACT‑style* planner inside **LangGraph**:
- **Analyse** user query → derive atomic intents & target entity types.
- **Route** each intent to the matching Specialist Agent (parallel when possible).
- **Collect** JSON / structured payloads returned by sub‑agents.
- **Synthesise** a markdown answer + sources; stream back to chat UI.
- Maintains a light memory store of recent sub‑results to avoid duplicate DB hits in the same session.![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.007.png)
3. **MCP & Tool Layer (unchanged)**

┌───────────────┐    LangGraph           ┌─────────────────────────┐ │ cancers coll. │←──CancerAgent Tools──→│  DB MCP Server          │ │ genes  coll.  │←──GeneAgent  Tools──→ │  (single process)       │ │ drugs  coll.  │←──DrugAgent  Tools──→ │ • exposes 12 tools      │ │ drugs\_india   │←──DrugINAgentTools──→ │ • role‑based auth       │ └───────────────┘                        └─────────────────────────┘![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.008.png)![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.009.png)

4. **End‑to‑End Query Flow**

graph TD![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.010.png)

`    `UserQuery["User\nquestion"] -->|1. send| MainAgent["Query‑Orchestrator"]     MainAgent -->|2a. cancer terms| CancerAgent

`    `MainAgent -->|2b. gene terms| GeneAgent

`    `MainAgent -->|2c. drug terms| DrugAgent

`    `MainAgent -->|2d. Indian drug terms| DrugIndiaAgent

`    `CancerAgent -->|3.| Cancers[(cancers)]

`    `GeneAgent -->|3.| Genes[(genes)]

`    `DrugAgent -->|3.| Drugs[(drugs)]

`    `DrugIndiaAgent -->|3.| DrugsIN[(drugs\_india)]

`    `Cancers -->|4.| CancerAgent

`    `Genes -->|4.| GeneAgent

`    `Drugs -->|4.| DrugAgent

`    `DrugsIN -->|4.| DrugIndiaAgent

`    `CancerAgent -->|5.| MainAgent

`    `GeneAgent -->|5.| MainAgent

`    `DrugAgent -->|5.| MainAgent

`    `DrugIndiaAgent -->|5.| MainAgent

`    `MainAgent -->|6. summary| Answer["Chatbot\nreply"]![ref1]

5. **Tool Design Examples (pseudo‑Python)**

@mcp.tool(namespace="cancers")![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.012.png)

def search\_cancer(name: str, fields: list[str] = ["summary", "incidence"]):

return db.cancers.find\_one({"name": name}, {f: 1 for f in fields})

@mcp.tool(namespace="genes")![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.013.png)

def get\_gene\_variants(hugo\_symbol: str):

return db.genes.aggregate([...])![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.014.png)

6. **Implementation Checklist (unchanged core steps)**
   1. **Refactor DB MCP Server** with namespaced tools.
   1. **Build Specialist Agents** with filtered toolsets.
   1. **Construct LangGraph DAG** for the orchestrator.
   1. **Integrate** into existing chatbot.
   1. **CI updates**.
   1. **Security** & **Observability** hooks.![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.015.png)
7. **Advantages of Collection‑Centric Agents**
- **Separation of concerns** → simpler prompts, smaller context windows per sub‑agent.
- **Granular scaling** → heavy gene queries won’t starve cancer‑lookups.
- **Easier schema evolution** → only the owning agent updates prompts/tests.
- **Targeted fine‑tuning** → can train retrieval augmentation per domain.![ref1]
8. **Potential Enhancements**
- **Add RefinerAgent** to post‑process conflicting drug vs gene info.
- **Graph‑aware Planner** that leverages schema‑linking (PK/FK) to decide join‑heavy queries.
- **Vector Cache** of frequent answers per collection; invalidate on collection writes.![](Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.016.png)
3

[ref1]: Aspose.Words.b74f83ef-1434-4128-b545-bb1a26929f8a.011.png
