# =============================================================================
# SHARED PROMPT BUILDING BLOCKS
# =============================================================================

JSON_RESPONSE_INSTRUCTIONS = """
Return ONLY valid JSON.

Do NOT:
- Wrap JSON in markdown
- Use ```json
- Add explanations
- Add comments
- Add text before or after the JSON

Output must be parseable JSON.
"""


GROUNDING_RULES = """
STRICT GROUNDING RULES:

1. Use ONLY information present in the provided evidence chunks.

2. Never invent:
   - names
   - dates
   - locations
   - legal conclusions
   - property details
   - document references

3. If information is missing:
   Write exactly:
   "Not found in provided documents."

4. If OCR text appears corrupted, incomplete, or illegible:
   Write:
   "Unclear from source document."

5. Every factual statement must cite:
   [chunk_id, page X]

6. Do not use outside knowledge.

7. Confidence levels:
   HIGH   = directly supported by clear evidence
   MEDIUM = supported but partially incomplete
   LOW    = weak or unclear evidence
"""


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

BASE_SYSTEM_PROMPT = f"""
You are an AI legal document analyst.

Your responsibility is to generate grounded legal-style drafts
from retrieved document evidence.

{GROUNDING_RULES}

Be concise, structured, and evidence-driven.
"""


FEEDBACK_SYSTEM_PROMPT = f"""
You are an AI system that learns from human edits.

Your task is to identify reusable editing patterns
that can improve future drafts.

Rules:

- Focus on terminology changes
- Focus on formatting preferences
- Focus on recurring section additions/removals
- Ignore one-off factual corrections
- Ignore document-specific changes

{JSON_RESPONSE_INSTRUCTIONS}
"""


# =============================================================================
# CASE FACT SUMMARY
# =============================================================================

CASE_FACT_SUMMARY_PROMPT = """
Generate a Case Fact Summary using ONLY the evidence below.

Retrieved Evidence:
{evidence_block}

Learned Patterns:
{learned_patterns}

Required Format:

--------------------------------------------------
CASE FACT SUMMARY
--------------------------------------------------

1. PARTIES INVOLVED
- Details
- Confidence: HIGH/MEDIUM/LOW
- Source: [chunk_id, page X]

2. KEY DATES AND TIMELINE
- Chronological events
- Confidence: HIGH/MEDIUM/LOW
- Source: [chunk_id, page X]

3. SUBJECT MATTER
- What the matter concerns
- Confidence: HIGH/MEDIUM/LOW
- Source: [chunk_id, page X]

4. KEY FACTS
- Bullet list
- Confidence: HIGH/MEDIUM/LOW
- Source: [chunk_id, page X]

5. DOCUMENTS REFERENCED
- Bullet list
- Source: [chunk_id, page X]

6. UNRESOLVED OR UNCLEAR ITEMS
- Missing information
- OCR issues
- Ambiguous sections

--------------------------------------------------
GROUNDING NOTE:
All statements are derived solely from retrieved chunks.
--------------------------------------------------
"""


# =============================================================================
# TITLE REVIEW SUMMARY
# =============================================================================

TITLE_REVIEW_PROMPT = """
Generate a Title Review Summary using ONLY the evidence below.

Retrieved Evidence:
{evidence_block}

Learned Patterns:
{learned_patterns}

Required Format:

--------------------------------------------------
TITLE REVIEW SUMMARY
--------------------------------------------------

1. PROPERTY DETAILS
- Address
- Parcel / survey number
- Legal description
- Confidence: HIGH/MEDIUM/LOW
- Source: [chunk_id, page X]

2. REGISTERED OWNER
- Current owner
- Confidence: HIGH/MEDIUM/LOW
- Source: [chunk_id, page X]

3. ENCUMBRANCES AND LIENS
- Mortgages
- Easements
- Liens
- Source: [chunk_id, page X]

4. CHAIN OF TITLE
- Ownership history
- Source: [chunk_id, page X]

5. FLAGS AND ISSUES
- Gaps
- Inconsistencies
- Risks
- Source: [chunk_id, page X]

6. UNRESOLVED OR UNCLEAR ITEMS
- Missing information
- OCR uncertainty
- Unclear ownership records

--------------------------------------------------
GROUNDING NOTE:
All statements are derived solely from retrieved chunks.
--------------------------------------------------
"""


# =============================================================================
# INTERNAL MEMO
# =============================================================================

INTERNAL_MEMO_PROMPT = """
Generate a First-Pass Internal Memo using ONLY the evidence below.

Retrieved Evidence:
{evidence_block}

Learned Patterns:
{learned_patterns}

Document ID:
{doc_id}

Current Date:
{current_date}

Required Format:

--------------------------------------------------
INTERNAL MEMO — FIRST PASS
--------------------------------------------------

TO: Legal Review Team

FROM: AI Document Analyst

RE: {doc_id}

DATE: {current_date}

SUBJECT SUMMARY

One paragraph summary.

Confidence: HIGH/MEDIUM/LOW

Source:
[chunk_id, page X]

KEY OBSERVATIONS

1. Observation
   Source: [chunk_id, page X]

2. Observation
   Source: [chunk_id, page X]

3. Observation
   Source: [chunk_id, page X]

ACTION ITEMS

1. Verification needed
2. Missing information
3. Additional review required

DISCLAIMER

This memo is AI-generated and intended only as a
first-pass internal review document.
"""


# =============================================================================
# DOCUMENT CHECKLIST
# =============================================================================

DOCUMENT_CHECKLIST_PROMPT = """
Generate a grounded Document Checklist.

Retrieved Evidence:
{evidence_block}

Learned Patterns:
{learned_patterns}

Document ID:
{doc_id}

Current Date:
{current_date}

Required Format:

--------------------------------------------------
DOCUMENT CHECKLIST
--------------------------------------------------

DOCUMENT:
{doc_id}

REVIEWED ON:
{current_date}

CHECKLIST

[ ] Party names clearly identified
Found: Yes / No / Partial
Source: [chunk_id, page X]

[ ] Key dates present
Found: Yes / No / Partial
Source: [chunk_id, page X]

[ ] Subject matter clearly stated
Found: Yes / No / Partial
Source: [chunk_id, page X]

[ ] Signatures or execution details present
Found: Yes / No / Partial
Source: [chunk_id, page X]

[ ] Referenced documents listed
Found: Yes / No / Partial
Source: [chunk_id, page X]

[ ] No illegible critical sections
Found: Yes / No / Partial
Source: [chunk_id, page X]

SUMMARY

- Total items checked: 6
- Items found: X
- Items missing: X

--------------------------------------------------
GROUNDING NOTE:
Checklist generated only from retrieved evidence.
--------------------------------------------------
"""


# =============================================================================
# PATTERN EXTRACTION
# =============================================================================

PATTERN_EXTRACTION_PROMPT = f"""
Analyze the operator edits below.

Original Draft:
{{original_draft}}

Edited Draft:
{{edited_draft}}

Extract reusable patterns.

Schema:

[
  {{
    "pattern_id": "pat_001",
    "pattern_type": "terminology",
    "description": "Use Registered Owner instead of Owner",
    "original_phrasing": "Owner",
    "preferred_phrasing": "Registered Owner",
    "frequency": 1
  }}
]

Rules:

- Extract only reusable patterns.
- Ignore document-specific factual corrections.
- Ignore spelling fixes.
- Ignore one-time edits.
- If no reusable patterns exist, return []

{JSON_RESPONSE_INSTRUCTIONS}
"""