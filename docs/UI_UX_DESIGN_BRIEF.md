# HireFlow — UI/UX Design System & Specification Brief

---

## 1. Executive Design Vision & Language

### 1.1 Philosophy: "FlowGlass Intelligence"
HireFlow’s visual and interaction design embodies **executive clarity, calm intelligence, and zero-cognitive-overload ergonomics**. Built for high-volume technical recruiters and engineering directors, the interface rejects noisy, childish gamification in favor of a sleek, dark-mode-first aesthetic inspired by high-end financial terminals and developer-centric intelligence suites.

### 1.2 Core Design Principles
1. **Evidence-First Information Density:** Every score, rating, or recommendation is visually tethered to inspectable evidence badges and expandable citation cards.
2. **Deterministic Feedback Loops:** Every agent execution, validation repair, and telemetry metric features an explicit visual state—recruiters are never left staring at an ambiguous spinner.
3. **Calm Ergonomics:** Deep slate foundations (`#090D16`, `#0F172A`) prevent eye fatigue during 8-hour recruiting shifts, highlighted with luminous electric cyan (`#06B6D4`) and deep indigo accents.
4. **Human Autonomy:** Primary decision gates (Advance, Reject, Override) are visually elevated as decisive human actions with distinct confirmation modals.

---

## 2. Color Palette & Token System

All color tokens are strictly locked to exact HEX and RGBA values:

```
[Background Foundations]
Canvas / Void:        #090D16   (Root app canvas)
Surface 1 (Card):     #0F172A   (Standard card container)
Surface 2 (Elevated): #1E293B   (Hover states, elevated cards, dropdowns)
Surface 3 (Modal):    #334155   (Modal overlays, tooltips, dialogs)
Glass Blur Base:      rgba(15, 23, 42, 0.75) with backdrop-filter: blur(16px)

[Border & Line Tokens]
Border Subtle:        #1E293B   (Subtle card dividers)
Border Standard:      #334155   (Default card borders)
Border Glass Edge:    rgba(255, 255, 255, 0.08) (High-end 1px top highlight)
Border Focus Cyan:    #06B6D4   (Interactive focus ring)

[Brand & Accent Tokens]
Cyan Primary:         #06B6D4   (Primary CTAs, active pills, indicators)
Cyan Glow:            rgba(6, 182, 212, 0.25)
Indigo Accent:        #6366F1   (Secondary accents, workflow links)
Electric Blue:        #3B82F6   (Technical depth badges, search vectors)
Brand Gradient:       linear-gradient(135deg, #06B6D4 0%, #3B82F6 50%, #6366F1 100%)

[Typography Tokens]
Text Primary:         #F8FAFC   (Headers, primary labels, main values)
Text Secondary:       #94A3B8   (Body copy, descriptions, sub-headers)
Text Muted:           #64748B   (Timestamps, inactive icons, placeholders)
Text Inverted:        #090D16   (Buttons with light backgrounds)

[Semantic Status Tokens]
Match High / Success: #10B981   (Score >= 80, confirmed skills, advance gate)
Match High Glow:      rgba(16, 185, 129, 0.15)
Match Mid / Warning:  #F59E0B   (Score 60–79, identified skill gaps, review needed)
Match Mid Glow:       rgba(245, 158, 11, 0.15)
Match Low / Danger:   #EF4444   (Score < 60, rejection gate, tamper violation)
Match Low Glow:       rgba(239, 68, 68, 0.15)
Info / Telemetry:     #0EA5E9   (Token stats, live connection pulses)

[Question Taxonomy Category Tokens]
Technical Depth:      #3B82F6   (Badge BG: rgba(59, 130, 246, 0.12), Text: #60A5FA)
Gap Probe:            #EC4899   (Badge BG: rgba(236, 72, 153, 0.12), Text: #F472B6)
Behavioral:           #10B981   (Badge BG: rgba(16, 185, 129, 0.12), Text: #34D399)
Culture Fit:          #8B5CF6   (Badge BG: rgba(139, 92, 246, 0.12), Text: #A78BFA)
Situational:          #F59E0B   (Badge BG: rgba(245, 158, 11, 0.12), Text: #FBBF24)
```

---

## 3. Typography Hierarchy

The type system pairs modern geometric authority with high-legibility sans-serif text and technical monospace numbers.

- **Display & Section Headers:** `Plus Jakarta Sans`, sans-serif
- **UI Controls, Tables, Body Copy:** `Inter`, -apple-system, sans-serif
- **Telemetry, Token Counts, Code, Excerpts:** `JetBrains Mono`, monospace

| Style Name | Font Family | Size | Weight | Line Height | Letter Spacing | Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Hero Display** | Plus Jakarta Sans | 32px (`2rem`) | 700 (Bold) | 40px | -0.02em | Main page titles, Dossier names |
| **Heading 1** | Plus Jakarta Sans | 24px (`1.5rem`) | 600 (SemiBold) | 32px | -0.01em | Dashboard sections, Modal titles |
| **Heading 2** | Plus Jakarta Sans | 18px (`1.125rem`) | 600 (SemiBold) | 26px | -0.005em | Card headers, Drawer titles |
| **Heading 3** | Plus Jakarta Sans | 15px (`0.9375rem`) | 600 (SemiBold) | 22px | 0 | Category headers, Widget labels |
| **Body Primary** | Inter | 14px (`0.875rem`) | 400 (Regular) | 20px | 0 | General interface copy, reasoning text |
| **Body Bold** | Inter | 14px (`0.875rem`) | 600 (SemiBold) | 20px | 0 | Table cell primary text, button text |
| **Caption / Meta**| Inter | 12px (`0.75rem`) | 500 (Medium) | 16px | +0.01em | Tag labels, timestamps, tooltips |
| **Code / Data** | JetBrains Mono | 12px (`0.75rem`) | 400 (Regular) | 18px | 0 | Token metrics, raw citations, IDs |

---

## 4. Spacing Rules & Grid System

HireFlow strictly adheres to an **8-point geometric scale** for layout rhythm:

- `space-1`: `4px` (`0.25rem`) — Micro-gaps between badges and icons
- `space-2`: `8px` (`0.5rem`) — Badge padding, button icon gaps
- `space-3`: `12px` (`0.75rem`) — Compact card padding, table cell vertical padding
- `space-4`: `16px` (`1rem`) — Standard component padding, input field height offsets
- `space-6`: `24px` (`1.5rem`) — Card padding, modal internal spacing
- `space-8`: `32px` (`2rem`) — Grid column gaps, section vertical separation
- `space-12`: `48px` (`3rem`) — Major view container padding
- `space-16`: `64px` (`4rem`) — Canvas margins

### Border Radius Tokens
- `radius-sm`: `4px` (Code blocks, micro badges)
- `radius-md`: `8px` (Standard inputs, buttons, table rows)
- `radius-lg`: `12px` (Cards, dropdowns, telemetry panels)
- `radius-xl`: `16px` (Modals, evidence drawer, candidate dossiers)
- `radius-full`: `9999px` (Pills, score rings, avatars)

---

## 5. Layout & Key Components Specification

---

### 5.1 Sidebar Navigation
- **Width:** Expanded `260px`, Collapsed `72px` (animated via `transition: width 200ms ease-in-out`).
- **Surface:** `#090D16` with a `1px` right border `#1E293B`.
- **Header:** HireFlow brand logo (Cyan gradient icon with white bold logotype), version chip `v1.0-mvp`.
- **Navigation Items:**
  - `Jobs & Requisitions` (`Briefcase` icon)
  - `Candidates Matrix` (`Users` icon)
  - `Interview Workspace` (`Mic` icon)
  - `Audit & Telemetry` (`ShieldCheck` icon)
  - `Settings` (`Settings` icon)
- **Active State Behavior:** Active link receives a subtle cyan glow background (`rgba(6, 182, 212, 0.08)`), white text (`#F8FAFC`), and an animated `3px` solid `#06B6D4` left indicator bar.
- **Footer:** Recruiter Profile Card showing current demo persona (*Sarah Jenkins / Senior Recruiter*) with a quick single-click Persona Switcher modal trigger.

---

### 5.2 Recruiter Dashboard
- **Top Metric Cards (Grid of 4):**
  1. *Active Requisitions:* Total open jobs with live candidate volume.
  2. *Top Match Candidates:* Count of candidates with score $\ge 80$.
  3. *Average Match Fidelity:* Percentage gauge of portfolio fit.
  4. *Hours Saved This Week:* Real-time calculation based on automated screening cycles.
- **Card Styling:** Surface `#0F172A`, `1px` border `#334155`, top highlight `rgba(255, 255, 255, 0.05)`, padding `20px`.
- **Score Distribution Chart Widget:** SVG Bar Chart color-coded by score band:
  - High Match ($\ge 80$): Emerald `#10B981`
  - Moderate Match (60–79): Amber `#F59E0B`
  - Low Match ($< 60$): Rose `#EF4444`
- **Recent Activity Feed:** Real-time stream of parsed resumes, completed interviews, and recorded human decisions.

---

### 5.3 Candidate Cards & Matching Matrix
- **Layout:** Responsive 2-column or 3-column card grid, or dense table view toggle.
- **Card Anatomy:**
  - **Header:** Candidate Name (`#F8FAFC`, 16px SemiBold), current title, target role chip, and application date.
  - **Score Ring Component:** Circular SVG gauge (diameter `56px`, stroke `5px`) displaying overall match score (0–100) with animated fill and color grading.
  - **Reasoning Snippet:** 2-line clamped summary (`#94A3B8`, 13px) explaining the score based on textual evidence.
  - **Confirmed Skills Section:** Flex row of pill badges (`rgba(16, 185, 129, 0.12)`, text `#10B981`, checkmark icon `✓`).
  - **Identified Gaps Section:** Flex row of outline badges (`rgba(245, 158, 11, 0.12)`, text `#F59E0B`, alert icon `!`).
  - **Action Footer:** Dual buttons:
    - `"Inspect Evidence"` (Secondary button with magnifying glass icon).
    - `"Prepare Interview"` (Primary Cyan button).

---

### 5.4 Candidate Detail Page & Dossier View
- **Header Banner:** Candidate name, contact email/phone, target job title, match score badge, and human status pill (`Under Review`, `Advanced`, `Rejected`).
- **Tabbed Sub-Navigation:**
  1. `Executive Overview` (Match scorecard, verified competencies, missing gaps).
  2. `Resume Evidence` (Direct PDF text layer viewer with citation markers).
  3. `Interview Transcript` (Full turn-by-turn dialogue with speaker tagging).
  4. `Rubric Evaluation` (Question-by-question scoring and commentary).
  5. `Audit Log` (Inference calls, token counts, and recruiter actions).
- **Sticky Human Decision Gate:** Persistent bottom floating bar:
  - Rationale input field: `"Optional recruiter notes for decision..."`
  - Action buttons:
    - `"Advance to Final Round"` (Green `#10B981`, checks icon).
    - `"Request Further Follow-up"` (Amber `#F59E0B`).
    - `"Reject with Feedback"` (Red outline `#EF4444`).

---

### 5.5 Match Visualization: Dual-Concentric Score Ring
- **Component:** `ScoreRing.jsx`
- **Design:** Double SVG circle ring:
  - *Outer Ring:* Represents **Vector Semantic Similarity** (`stroke: #3B82F6`).
  - *Inner Ring:* Represents **Heuristic Skill & Experience Overlap** (`stroke: #06B6D4`).
- **Center Value:** Weighted composite match score (0–100) rendered in `Plus Jakarta Sans` 700 Bold.
- **Interaction:** Hovering reveals a precision breakdown tooltip:
  - Vector Distance: `0.84`
  - Skill Overlap: `80% (8 of 10 required skills matched)`
  - Experience Alignment: `5.5 yrs vs 5.0 yrs min required`

---

### 5.6 Candidate Evidence Drawer (Slide-Over)
- **Behavior:** Smoothly slides in from the right viewport edge (`width: 520px`, backdrop overlay `rgba(0, 0, 0, 0.6)`).
- **Header:** Candidate Name + target requirement being inspected.
- **Split Inspector:**
  - *Top Half (Claim vs Requirement):* Required skill from JD vs what candidate claimed.
  - *Bottom Half (Verbatim Resume Citation):* Exact blockquote excerpt from candidate's original resume file with highlighted keywords (`background: rgba(6, 182, 212, 0.2)`).
  - *Confidence Indicator:* High / Moderate / Inferred badge.
  - *Human Override Control:* `"Dispute / Manually Confirm Skill"` button allowing recruiter to override false-negative gaps.

---

### 5.7 Live Interview Workspace
- **Dual-Pane Cockpit Layout:**
  - **Left Pane (60% — Candidate Screening Station):**
    - Clean, focused interface for candidate response submission.
    - Active question card displaying current topic and question number (`Question 3 of 5`).
    - Text response input area or audio recording wave visualizer.
    - Submit response button with barge-in / skip options.
  - **Right Pane (40% — Recruiter Live Telemetry Monitor):**
    - **Header:** Live status badge (`STREAMING ACTIVE` in pulsating emerald green).
    - **Anti-Tamper Monitor:** Real-time security banner (`INTEGRITY STATUS: VERIFIED` green or `TAMPER ATTEMPT DETECTED` red with immediate alarm pulse).
    - **Live Transcript Stream:** Auto-scrolling conversation feed differentiating `AI Agent` (Cyan avatar, left-aligned) and `Candidate` (White card, right-aligned).
    - **Question Progress Tracker:** Vertical stepper showing completed, active, and upcoming topics.

---

### 5.8 AI Activity Panel & Observability Widget
- **Location:** Collapsible drawer accessible from the top navbar or sidebar footer.
- **Contents:**
  - Current active agent pill (e.g., `Agent: JDInclusivityAuditor`).
  - Real-time token burn odometer: Prompt Tokens, Completion Tokens, Total Tokens.
  - Latency ticker: Current inference duration (`1,240 ms`).
  - Session Cost Accumulator: `$0.042` (live cost based on model token rates).
  - System Health Indicator: Green dot (`All inference providers operational`).

---

### 5.9 Tables
- **Styling:**
  - Header: `#0F172A`, text `#94A3B8`, uppercase 12px Medium, `1px` border-b `#334155`.
  - Rows: `#090D16` base, alternating subtle row striping `#0D1322`.
  - Hover: Row background shifts to `#1E293B` with a `150ms` transition.
  - Cell Padding: `12px 16px`.
  - Border: Subtle horizontal divider `1px solid #1E293B`.

---

### 5.10 Buttons & Interactive Elements
- **Primary Button (HireFlow Cyan):**
  - Background: `#06B6D4`, text `#090D16` (Bold), border radius `8px`.
  - Hover: Background `#0891B2`, subtle box-shadow `0 0 16px rgba(6, 182, 212, 0.35)`.
  - Active: Scale `0.98`.
  - Disabled: Background `#1E293B`, text `#64748B`, cursor `not-allowed`.
- **Secondary Button (Elevated Glass):**
  - Background: `#1E293B`, text `#F8FAFC`, border `1px solid #334155`.
  - Hover: Background `#334155`, border `#475569`.
- **Destructive Button (Rose):**
  - Background: `rgba(239, 68, 68, 0.12)`, text `#EF4444`, border `1px solid rgba(239, 68, 68, 0.3)`.
  - Hover: Background `#EF4444`, text `#FFFFFF`.
- **Icon Button:**
  - Square `36px x 36px`, rounded `8px`, centered Lucide icon, subtle hover highlight.

---

### 5.11 Inputs, Selects & Dropzones
- **Text Input & Textareas:**
  - Background: `#090D16`, border `1px solid #334155`, text `#F8FAFC`.
  - Placeholder: `#64748B`.
  - Focus State: Border color `#06B6D4`, outline none, box-shadow `0 0 0 2px rgba(6, 182, 212, 0.2)`.
- **File Upload Dropzone:**
  - Border: `2px dashed #334155`, background `rgba(15, 23, 42, 0.5)`, rounded `16px`, padding `32px`.
  - Drag Over State: Border `#06B6D4`, background `rgba(6, 182, 212, 0.05)`.
  - File Chips: Removable pills with file name, size, and green checkmark.

---

### 5.12 Modals & Dialogs
- **Overlay:** `rgba(0, 0, 0, 0.75)` with `backdrop-filter: blur(8px)`.
- **Modal Container:**
  - Surface: `#0F172A`, border `1px solid #334155`, rounded `16px`, padding `24px`.
  - Entrance Animation: Scale `0.95` to `1.0`, opacity `0` to `1` (`200ms ease-out`).
  - Header: 20px SemiBold title with close (`✕`) icon button in top-right.
  - Footer: Right-aligned Cancel and Confirm action buttons.

---

## 6. Feedback & Exception States

### 6.1 Loading States
- **Skeleton Loaders:** CSS pulse animation (`@keyframes shimmer`) over `#1E293B` shapes mimicking exact cards, avatars, and table rows.
- **Determinate Progress Bar:** Gradient bar (`#06B6D4` to `#3B82F6`) displaying real-time percentage across ingestion queues.

### 6.2 Empty States
- **Container:** Centered column layout with `48px` vertical padding.
- **Illustration:** Muted vector SVG with subtle glass glow.
- **Typography:** 16px SemiBold title (`#F8FAFC`) + 14px descriptive explanation (`#94A3B8`).
- **Action:** Prominent Primary Button inviting the user to take the initial action (e.g., *"Upload Your First Candidate"*).

### 6.3 Error States
- **Card-Level Alert:** Amber/Red alert banner with warning icon, error description, and a single-click `"Retry Action"` button.
- **Field-Level Validation:** `1px solid #EF4444` border with 12px error copy beneath the input.
- **AI Failure Notification:** Floating toast banner indicating model timeout with an automated countdown to the next repair attempt (`"Retrying with fast fallback model in 3s..."`).

---

## 7. Responsive Behavior & Breakpoints

HireFlow is optimized for desktop and tablet recruitment stations:

| Breakpoint | Dimensions | Layout Adjustments |
| :--- | :--- | :--- |
| **Desktop Ultra / Wide (`2xl`)** | $\ge 1536\text{px}$ | 4-column candidate matrix; permanent live telemetry sidebar visible. |
| **Desktop Standard (`xl`)** | $1280\text{px} - 1535\text{px}$ | Standard 3-column candidate grid; dual-pane interview workspace. |
| **Laptop / Small Desktop (`lg`)** | $1024\text{px} - 1279\text{px}$ | 2-column candidate grid; sidebar collapses to icon-only mode (`72px`). |
| **Tablet (`md`)** | $768\text{px} - 1023\text{px}$ | Single-column candidate stack; evidence drawer occupies full screen width. |
| **Mobile (`sm`)** | $< 768\text{px}$ | View-only dossier mode; candidate screening station formatted for single-turn inputs. |

---

## 8. Accessibility & Compliance Standards (WCAG 2.1 AA)

1. **Color Contrast Ratios:**
   - Text Primary (`#F8FAFC`) against Surface (`#0F172A`): Ratio **14.2:1** (Exceeds AAA standard).
   - Text Secondary (`#94A3B8`) against Surface (`#0F172A`): Ratio **5.6:1** (Exceeds AA standard).
   - Accent Cyan (`#06B6D4`) against Dark Canvas (`#090D16`): Ratio **7.8:1**.
2. **Keyboard Navigability:**
   - Full tab-index traversal across all buttons, inputs, table rows, and modal triggers.
   - Visible focus indicator: `2px solid #06B6D4` with `2px` offset.
   - `Escape` key closes all slide-over drawers and modals.
3. **Screen Reader Semantic Hierarchy:**
   - Proper HTML5 landmark tags (`<nav>`, `<main>`, `<aside>`, `<header>`).
   - All interactive icons equipped with descriptive `aria-label` tags (e.g., `aria-label="Inspect candidate evidence"`).
   - Live telemetry regions marked with `aria-live="polite"` for streaming transcripts.

---

## Summary Approval
This UI/UX Design System Brief defines the complete aesthetic, layout, component, and interaction standard for **HireFlow**. All frontend components, layouts, and interactive behaviors must strictly implement the color tokens, type scales, and interaction rules specified in this document.
