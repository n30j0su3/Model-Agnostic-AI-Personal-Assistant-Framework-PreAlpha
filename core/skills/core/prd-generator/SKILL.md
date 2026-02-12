---
name: prd-generator
description: Generates structured Product Requirements Documents with user stories, acceptance criteria, and stakeholder alignment.
license: MIT
metadata:
  author: opencode
  version: "1.1"
compatibility: OpenCode, Claude Code, Gemini CLI, Codex
---

# PRD Generator Skill

Convert product ideas into clear, actionable requirements that engineering teams can build from.

## Instructions

### 1. PRD Structure
Use the standard structure and fill each section with concise, testable statements.

```
TITLE: [Feature Name]
Author: [Owner] | Status: [Draft/Review/Approved]
Last Updated: [Date]
Agents: [Roles + owners]
Backlog IDs: [BL-###, BL-###]

1. OVERVIEW
   - Problem Statement
   - Proposed Solution
   - Success Metrics

2. GOALS & NON-GOALS
   - Goals
   - Non-Goals

3. USERS & CONTEXT
   - Primary Users
   - Usage Context
   - Constraints

4. REQUIREMENTS
   - User Stories
   - Functional Requirements
   - Non-Functional Requirements
   - Acceptance Criteria (per story)

5. DESIGN & TECH
   - User Flows
   - Wireframes/Mockups
   - Technical Considerations

6. BACKLOG TRACEABILITY
   - BL-### -> Requirement/Story mapping
   - Out-of-scope items linked to backlog if deferred

7. DELIVERY
   - Milestones
   - Dependencies
   - Risks
   - Rollout/Release plan

8. APPENDIX
   - Research Data
   - Open Questions
```

### 2. User Story Format

```
As a [user type]
I want to [action]
So that [benefit]
```

Acceptance Criteria (Given-When-Then):

```
Given [context]
When [action]
Then [expected result]
```

### 3. Requirements Writing

- Use active verbs (display, calculate, send).
- Avoid vague terms (appropriate, reasonable).
- Each requirement must be testable and verifiable.
- Keep one requirement per statement.
- Include negative/edge cases where relevant.

Functional example:
"System shall send an email confirmation within 30 seconds of order completion."

Non-functional examples:
- Performance: page load < 2s
- Security: encryption at rest
- Availability: 99.9% uptime SLA
- Accessibility: WCAG 2.1 AA

### 4. Complexity Tiers

- Tier 1: Small feature (1-page PRD, single story, no dependencies)
- Tier 2: Medium feature (3-5 pages, multiple stories, some dependencies)
- Tier 3: Major initiative (10+ pages, cross-team dependencies)

### 5. Stakeholder Alignment

List stakeholders with interest, decision rights, and sign-off requirement.

## Output Format

- Deliver a complete PRD in plain markdown.
- Include user stories and acceptance criteria for every story.
- Include backlog IDs and agent roles in the header.

## Supported Commands

- "Generate a PRD for: <idea>"
- "Create user stories and acceptance criteria for: <feature>"
