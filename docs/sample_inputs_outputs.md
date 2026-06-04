# Sample Inputs and Outputs

## Sample Input

### Process Document

Request:

```json
{
  "filename": "sample.pdf"
}
```

Response:

```json
{
  "success": true,
  "doc_id": "doc_069741a9",
  "filename": "sample.pdf",
  "chunk_count": 15,
  "page_count": 7
}
```

---

## Draft Generation

Request:

```json
{
  "doc_id": "doc_069741a9",
  "draft_type": "case_fact_summary"
}
```

Response (Partial):

```text
CASE FACT SUMMARY

SUBJECT MATTER

The matter concerns the process and requirements
for generating legal-style drafts.

Source:
[doc_069741a9_p03_c006, page 3]
```

---

## Feedback Learning

Request:

```json
{
  "doc_id": "doc_069741a9",
  "draft_type": "case_fact_summary",
  "original_draft": "Owner",
  "edited_draft": "Registered Owner"
}
```

Result:

Pattern learned:

Owner
↓
Registered Owner

---

## Learning Statistics

Response:

```json
{
  "total_patterns": 1,
  "most_common_pattern": "Use 'Registered Owner' instead of 'Owner'",
  "max_frequency": 3
}
```
