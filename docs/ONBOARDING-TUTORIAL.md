# Onboarding Tutorial Planning Document

> **Backlog Item:** BL-101  
> **Version:** 1.0  
> **Created:** April 2026  
> **Status:** Planning  
> **Prerequisite:** [GETTING-STARTED.md](./GETTING-STARTED.md) (5-minute quick-start)

---

## 1. Learning Objectives

### Primary Objectives
After completing this tutorial, users will be able to:

| # | Objective | Success Criteria | Time Target |
|---|-----------|------------------|-------------|
| 1 | Navigate the framework interface | Access dashboard, start sessions, locate files | <1 min |
| 2 | Use core skills effectively | Invoke 3+ skills correctly with `@skill-name` syntax | <2 min |
| 3 | Understand session memory | Reference previous session content in current session | <1 min |
| 4 | Create basic workflows | Chain 2+ skills for a complete task | <1 min |
| 5 | Access help resources | Locate documentation, skills catalog, troubleshooting | <30 sec |

### Secondary Objectives
- Customize personal settings (language, AI provider)
- Create a new workspace for projects
- Export/backup personal data

### Success Definition
**User is "productive" when they can:**
- Start a session and ask their first question with skill invocation
- Understand where their data lives
- Know how to get help independently

**Target: Time-to-Productivity < 5 minutes**

---

## 2. Tutorial Structure (5 Sections Matching Skills Categories)

### Section 1: Document Processing Skills
**Duration:** 3-5 minutes (read + exercise)

| Skill | Use Case | Complexity |
|-------|----------|------------|
| `@pdf` | Read, extract, analyze PDF files | ⭐ Beginner |
| `@docx` | Create/edit Word documents | ⭐ Beginner |
| `@xlsx` | Spreadsheet operations | ⭐⭐ Intermediate |
| `@pptx` | PowerPoint presentations | ⭐⭐ Intermediate |
| `@csv-processor` | CSV manipulation | ⭐ Beginner |
| `@markdown-writer` | Consistent markdown docs | ⭐ Beginner |
| `@paper-summarizer` | Scientific paper analysis | ⭐⭐⭐ Advanced |

**Key Learning:** How to invoke skills with `@skill-name` syntax

---

### Section 2: Data & Visualization Skills
**Duration:** 3-5 minutes (read + exercise)

| Skill | Use Case | Complexity |
|-------|----------|------------|
| `@data-viz` | Charts, graphs, visualizations | ⭐⭐ Intermediate |
| `@etl` | Extract, Transform, Load operations | ⭐⭐⭐ Advanced |
| `@dashboard-pro` | Professional dashboard creation | ⭐⭐⭐ Advanced |

**Key Learning:** Connecting data sources to visual outputs

---

### Section 3: Task & Workflow Management Skills
**Duration:** 2-3 minutes (read + exercise)

| Skill | Use Case | Complexity |
|-------|----------|------------|
| `@task-management` | To-do lists, task tracking | ⭐ Beginner |
| `@decision-engine` | Local vs remote execution decisions | ⭐⭐⭐ Advanced |
| `@error-recovery` | Self-healing error handling | ⭐⭐ Intermediate |

**Key Learning:** Managing multi-step tasks and recovering from errors

---

### Section 4: Content Creation & Optimization Skills
**Duration:** 3-4 minutes (read + exercise)

| Skill | Use Case | Complexity |
|-------|----------|------------|
| `@prompt-improvement` | Optimize AI prompts | ⭐ Beginner |
| `@content-optimizer` | SEO, readability, engagement | ⭐ Beginner |
| `@prd-generator` | Product Requirements Documents | ⭐⭐ Intermediate |
| `@json-prompt-generator` | Structured JSON prompts | ⭐⭐ Intermediate |
| `@ui-ux-pro-max` | UI/UX design guidance | ⭐⭐⭐ Advanced |

**Key Learning:** Creating high-quality content with AI assistance

---

### Section 5: Advanced Skills & Customization
**Duration:** 4-5 minutes (read + exercise)

| Skill | Use Case | Complexity |
|-------|----------|------------|
| `@skill-discovery` | Find the right skill for your task | ⭐ Beginner |
| `@skill-creator` | Build custom skills | ⭐⭐⭐ Advanced |
| `@mcp-builder` | Create MCP servers | ⭐⭐⭐ Advanced |
| `@context-evaluator` | Evaluate response quality | ⭐⭐ Intermediate |
| `@python-standards` | Cross-platform Python scripts | ⭐⭐ Intermediate |

**Key Learning:** Extending the framework with custom capabilities

---

## 3. Interactive Exercises Ideas

### Exercise 1: First Skill Invocation (Section 1)
**Scenario:** "Extract text from a PDF report"
```
1. User has a sample PDF in their workspace
2. Tutorial guides: "Type: Use @pdf to summarize this document"
3. Success: User sees extracted content
4. Next: "Now try @docx to create a summary document"
```

**Interactive Element:** Guided prompt with placeholder text

---

### Exercise 2: Data Pipeline (Section 2)
**Scenario:** "Create a visualization from spreadsheet data"
```
1. User has sample data.csv in workspace
2. Tutorial guides:
   - "Type: Use @csv-processor to analyze the data"
   - "Then: Use @data-viz to create a chart"
3. Success: User sees generated chart
```

**Interactive Element:** Pre-loaded sample data files

---

### Exercise 3: Task Tracking (Section 3)
**Scenario:** "Create a project to-do list"
```
1. Tutorial guides: "Type: Use @task-management to create a task called 'Complete tutorial'"
2. Success: Task appears in tracking system
3. Follow-up: "Mark the task as complete"
```

**Interactive Element:** Visual task board that updates in real-time

---

### Exercise 4: Content Optimization (Section 4)
**Scenario:** "Improve a draft email"
```
1. User provides rough draft text
2. Tutorial guides: "Type: Use @content-optimizer to improve this email"
3. Success: Optimized version with explanations
```

**Interactive Element:** Side-by-side comparison (before/after)

---

### Exercise 5: Skill Discovery (Section 5)
**Scenario:** "Find the right skill for a task"
```
1. Tutorial presents scenario: "I need to process a JSON file"
2. User types: "Use @skill-discovery to find the right skill for JSON processing"
3. Success: System recommends appropriate skills
```

**Interactive Element:** Skill recommendation quiz

---

### Bonus Exercise: Skill Chaining
**Scenario:** Complete workflow combining multiple skills
```
Chain: @pdf → @task-management → @docx
1. Extract tasks from PDF meeting notes
2. Create tracked tasks
3. Generate summary document
```

---

## 4. Success Metrics

### Quantitative Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Time-to-first-skill | <2 minutes | Session timestamp analysis |
| Time-to-productivity | <5 minutes | User completes 3+ skill invocations |
| Tutorial completion rate | >80% | Exit checkpoint reached |
| Skill invocation accuracy | >90% | Correct `@skill-name` syntax |
| Error recovery rate | >75% | Users recover from errors without help |

### Qualitative Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| User confidence | High | Post-tutorial survey (1-5 scale, avg >4) |
| Feature discovery | Good | User knows 5+ skills exist |
| Documentation awareness | Good | User knows where to find help |
| Frustration level | Low | No repeated failed attempts |

### Analytics Implementation

```python
# Suggested tracking events
events = [
    "tutorial_started",
    "section_completed",
    "skill_invoked",
    "skill_invoked_correctly",
    "exercise_completed",
    "help_requested",
    "tutorial_completed",
    "time_spent_per_section"
]
```

### Success Dashboard

```
┌──────────────────────────────────────────────────────────────────────┐
│                      ONBOARDING ANALYTICS                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Time to Productivity:  [████████░░] 3.2 min (target: <5 min) ✅    │
│   Completion Rate:       [████████░] 85% (target: >80%) ✅           │
│   Skill Accuracy:        [█████████] 92% (target: >90%) ✅           │
│   User Confidence:        ⭐⭐⭐⭐☆ 4.2/5 (target: >4) ✅              │
│                                                                      │
│   Top Completed Sections:                                            │
│   1. Document Processing ████████████████████ 95%                   │
│   2. Task Management     ██████████████████   88%                   │
│   3. Data & Viz          ███████████████      82%                   │
│   4. Content Creation    █████████████        78%                   │
│   5. Advanced Skills     ████████████         65%                   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 5. Resource Requirements

### Documentation Resources

| Resource | Status | Owner | Priority |
|----------|--------|-------|----------|
| GETTING-STARTED.md | ✅ Complete | Framework Team | Prerequisite |
| ONBOARDING-TUTORIAL.md (this doc) | 📝 Planning | TBD | High |
| Tutorial content (5 sections) | ❌ Not started | TBD | High |
| Interactive exercise templates | ❌ Not started | TBD | Medium |
| Video walkthrough scripts | ❌ Not started | TBD | Low |
| FAQ expansion | ❌ Not started | TBD | Medium |

---

### Technical Resources

| Resource | Status | Owner | Priority |
|----------|--------|-------|----------|
| Sample PDF for exercises | ❌ Not created | TBD | High |
| Sample CSV/Excel for exercises | ❌ Not created | TBD | High |
| Sample markdown draft for exercises | ❌ Not created | TBD | Medium |
| Tutorial progress tracking | ❌ Not implemented | TBD | Low |
| Interactive prompt system | ❌ Not implemented | TBD | Low |
| Analytics event tracking | ❌ Not implemented | TBD | Medium |

---

### Infrastructure Requirements

| Requirement | Status | Notes |
|-------------|--------|-------|
| `/docs/onboarding/` directory | ❌ Create | New directory for tutorial assets |
| `/docs/onboarding/samples/` | ❌ Create | Sample files for exercises |
| Tutorial launcher script | ❌ Create | `core/scripts/tutorial.py` |
| Progress checkpoint system | ❌ Design | Track user progress |
| Completion certificate | ❌ Optional | Generate on completion |

---

### Human Resources

| Role | Time Estimate | Responsibilities |
|------|---------------|-----------------|
| Technical Writer | 8-12 hours | Write 5 tutorial sections |
| UX Designer | 4-6 hours | Design interactive exercises |
| Developer | 6-8 hours | Implement progress tracking |
| QA Tester | 4 hours | Test tutorial flow |
| Project Manager | 2 hours | Coordinate deliverables |

**Total Estimated Effort:** 24-32 hours

---

### Dependencies

```
GETTING-STARTED.md (prerequisite)
    │
    └──► ONBOARDING-TUTORIAL.md (this planning doc)
              │
              ├──► Tutorial Content (5 sections)
              │         │
              │         └──► Interactive Exercises
              │
              ├──► Sample Files
              │         │
              │         ├── sample.pdf
              │         ├── sample.csv
              │         └── sample-draft.md
              │
              └──► Progress Tracking (optional)
                        │
                        └──► Analytics Dashboard
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Sprint 1)
- [ ] Create `/docs/onboarding/` directory structure
- [ ] Write Section 1 (Document Processing)
- [ ] Create sample PDF and CSV files
- [ ] Implement basic tutorial launcher

### Phase 2: Core Content (Sprint 2)
- [ ] Write Sections 2-4 (Data, Tasks, Content)
- [ ] Create interactive exercise templates
- [ ] Add progress checkpoints

### Phase 3: Advanced + Polish (Sprint 3)
- [ ] Write Section 5 (Advanced Skills)
- [ ] Add skill-chaining exercise
- [ ] Implement completion tracking
- [ ] User testing and feedback

### Phase 4: Analytics (Optional)
- [ ] Add event tracking
- [ ] Create analytics dashboard
- [ ] A/B testing framework

---

## 7. Acceptance Criteria

### Definition of Done

- [ ] All 5 sections written and reviewed
- [ ] At least 3 interactive exercises per section
- [ ] Sample files available for all exercises
- [ ] Tutorial completable in <5 minutes
- [ ] Success metrics dashboard designed
- [ ] Documentation linked from main README
- [ ] GETTING-STARTED.md referenced as prerequisite
- [ ] User testing completed with >80% satisfaction

---

## 8. Related Documents

| Document | Relationship | Location |
|----------|--------------|----------|
| GETTING-STARTED.md | Prerequisite (quick-start) | `docs/GETTING-STARTED.md` |
| SKILLS.md | Skills reference | `core/skills/SKILLS.md` |
| README.md | Main documentation | `README.md` |
| UPDATE-GUIDE.md | Update procedures | `docs/UPDATE-GUIDE.md` |
| ROADMAP.md | Future plans | `ROADMAP.md` |

---

## 9. Notes & Considerations

### User Personas
1. **Complete Beginner:** Never used AI assistants, needs hand-holding
2. **AI-Familiar:** Used ChatGPT/Claude, new to local frameworks
3. **Developer:** Wants technical details, will skim

### Accessibility
- Provide text alternatives for all diagrams
- Ensure high contrast in visual elements
- Support screen readers for interactive elements

### Localization
- Design for English and Spanish (framework is bilingual)
- Keep text modular for easy translation
- Avoid idioms that don't translate well

### Maintenance
- Update when new skills are added
- Version tutorial with framework releases
- Collect user feedback continuously

---

*Document Status: Planning | Next: Implementation Planning Meeting*

---

**BL-101 Backlog Item: Onboarding Tutorial**

> *"El conocimiento verdadero trasciende a lo público."*
>
> — FreakingJSON