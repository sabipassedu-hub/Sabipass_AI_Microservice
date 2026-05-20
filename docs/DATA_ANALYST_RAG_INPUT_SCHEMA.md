# Data Analyst RAG Input Schema

This is the handoff format for past questions, worked solutions, and source
files that will feed SabiPass RAG.

The immediate MVP pipeline reads JSON files from `data/raw/mock/`. The real PDF
parser should produce the exact past-question shape below, so replacing the
mock loader later only changes the loader, not the downstream ingestion
pipeline.

## Delivery Package

Send one folder per delivery:

```text
data_delivery_YYYY_MM_DD/
  manifest.json
  past_questions/
    waec_mathematics_2024_paper_1.json
    jamb_mathematics_2023.json
  rag_documents/
    waec_mathematics_formula_notes.json
    algebra_worked_examples.json
  source_files/
    waec_mathematics_2024_paper_1.pdf
    jamb_mathematics_2023.pdf
```

Keep file names lowercase with underscores. Each JSON file must be valid UTF-8.

## Required RAG Metadata

Every question or chunk that enters retrieval must carry these fields:

```json
{
  "subject": "mathematics",
  "topic": "linear_equations",
  "difficulty": "easy",
  "exam_type": "WAEC",
  "academic_stage": "senior_secondary",
  "has_worked_solution": true,
  "year": 2024
}
```

Allowed values:

- `subject`: currently `mathematics`
- `exam_type`: `WAEC` or `JAMB`
- `academic_stage`: `junior_secondary` or `senior_secondary`
- `difficulty`: `foundation`, `easy`, `medium`, or `hard`
- `topic`: a canonical concept key from `data/processed/concept_registry.json`

If the exact topic is uncertain, use the closest broad parent topic and add the
uncertainty in the delivery manifest notes. Do not add extra fields to the
past-question JSON.

## Past Question JSON Schema

Each past-question JSON file should match this shape:

```json
{
  "parser_version": "pdf_parser_v1",
  "source_document": {
    "doc_id": "waec_math_2024_paper_1",
    "source_type": "pdf_parse",
    "subject": "mathematics",
    "exam_type": "WAEC",
    "academic_stage": "senior_secondary",
    "year": 2024
  },
  "questions": [
    {
      "question_id": "waec_math_2024_paper_1_q001",
      "page_number": 1,
      "topic": "linear_equations",
      "difficulty": "easy",
      "question_text": "If 3x + 4 = 19, find the value of x.",
      "answer_options": {
        "A": "3",
        "B": "4",
        "C": "5",
        "D": "6"
      },
      "correct_answer": "C",
      "has_worked_solution": true,
      "worked_solution": "Subtract 4 from both sides to get 3x = 15. Divide both sides by 3, so x = 5."
    }
  ]
}
```

Rules:

- `question_id` must be unique across all delivered files.
- `answer_options` must contain exactly `A`, `B`, `C`, and `D` for MCQ items.
- `correct_answer` must be one of `A`, `B`, `C`, or `D`.
- `worked_solution` is required when `has_worked_solution` is `true`.
- Keep equations and units exactly as they appear in the source.
- Do not summarize a question. Preserve the full wording.
- If a diagram is required, write `[DIAGRAM_REQUIRED: description]` inside
  `question_text` and include the original source PDF page.
- Do not add extra fields to `source_document` or `questions` in the MVP
  past-question JSON.

Formal schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://sabipass.local/schemas/past_question_parse.v1.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["parser_version", "source_document", "questions"],
  "properties": {
    "parser_version": { "type": "string", "minLength": 1 },
    "source_document": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "doc_id",
        "source_type",
        "subject",
        "exam_type",
        "academic_stage",
        "year"
      ],
      "properties": {
        "doc_id": { "type": "string", "minLength": 1 },
        "source_type": { "enum": ["pdf_parse", "mock_pdf_parse"] },
        "subject": { "const": "mathematics" },
        "exam_type": { "enum": ["WAEC", "JAMB"] },
        "academic_stage": {
          "enum": ["junior_secondary", "senior_secondary"]
        },
        "year": { "type": "integer", "minimum": 1900 }
      }
    },
    "questions": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "question_id",
          "page_number",
          "topic",
          "difficulty",
          "question_text",
          "answer_options",
          "correct_answer",
          "has_worked_solution",
          "worked_solution"
        ],
        "properties": {
          "question_id": { "type": "string", "minLength": 1 },
          "page_number": { "type": "integer", "minimum": 1 },
          "topic": { "type": "string", "minLength": 1 },
          "difficulty": {
            "enum": ["foundation", "easy", "medium", "hard"]
          },
          "question_text": { "type": "string", "minLength": 1 },
          "answer_options": {
            "type": "object",
            "additionalProperties": false,
            "required": ["A", "B", "C", "D"],
            "properties": {
              "A": { "type": "string", "minLength": 1 },
              "B": { "type": "string", "minLength": 1 },
              "C": { "type": "string", "minLength": 1 },
              "D": { "type": "string", "minLength": 1 }
            }
          },
          "correct_answer": { "enum": ["A", "B", "C", "D"] },
          "has_worked_solution": { "type": "boolean" },
          "worked_solution": { "type": "string", "minLength": 1 }
        }
      }
    }
  }
}
```

## RAG Support Document Schema

Use this for curriculum notes, formula sheets, examiner notes, and extra worked
examples that are not direct past-question rows.

```json
{
  "document_id": "waec_math_formula_notes_v1",
  "source_type": "formula_sheet",
  "source_file_name": "waec_mathematics_formula_notes.pdf",
  "source_file_sha256": "replace_with_file_hash",
  "subject": "mathematics",
  "exam_type": "WAEC",
  "academic_stage": "senior_secondary",
  "year": 2024,
  "title": "WAEC Mathematics Formula Notes",
  "chunks": [
    {
      "chunk_id": "waec_math_formula_notes_v1_c001",
      "topic": "trigonometric_ratios",
      "difficulty": "foundation",
      "has_worked_solution": false,
      "chunk_type": "concept_note",
      "content": "For a right-angled triangle, sin theta = opposite / hypotenuse, cos theta = adjacent / hypotenuse, and tan theta = opposite / adjacent.",
      "review_notes": ""
    }
  ]
}
```

Allowed `source_type` values:

- `curriculum_note`
- `formula_sheet`
- `worked_example`
- `examiner_report`
- `syllabus`
- `pdf_parse`

Allowed `chunk_type` values:

- `concept_note`
- `formula`
- `worked_solution`
- `exam_tip`
- `definition`

Chunking rules:

- One chunk should teach one concept or one worked example.
- Keep each chunk below 600 words.
- Never split a worked solution in the middle of a math step.
- Include source page numbers in `review_notes` when possible.

Formal schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://sabipass.local/schemas/rag_support_document.v1.json",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "document_id",
    "source_type",
    "subject",
    "exam_type",
    "academic_stage",
    "year",
    "title",
    "chunks"
  ],
  "properties": {
    "document_id": { "type": "string", "minLength": 1 },
    "source_type": {
      "enum": [
        "curriculum_note",
        "formula_sheet",
        "worked_example",
        "examiner_report",
        "syllabus",
        "pdf_parse"
      ]
    },
    "source_file_name": { "type": "string" },
    "source_file_sha256": { "type": "string" },
    "subject": { "const": "mathematics" },
    "exam_type": { "enum": ["WAEC", "JAMB"] },
    "academic_stage": { "enum": ["junior_secondary", "senior_secondary"] },
    "year": { "type": "integer", "minimum": 1900 },
    "title": { "type": "string", "minLength": 1 },
    "chunks": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "chunk_id",
          "topic",
          "difficulty",
          "has_worked_solution",
          "chunk_type",
          "content"
        ],
        "properties": {
          "chunk_id": { "type": "string", "minLength": 1 },
          "topic": { "type": "string", "minLength": 1 },
          "difficulty": {
            "enum": ["foundation", "easy", "medium", "hard"]
          },
          "has_worked_solution": { "type": "boolean" },
          "chunk_type": {
            "enum": [
              "concept_note",
              "formula",
              "worked_solution",
              "exam_tip",
              "definition"
            ]
          },
          "content": { "type": "string", "minLength": 1 },
          "review_notes": { "type": "string" }
        }
      }
    }
  }
}
```

## Manifest Schema

Each delivery should include a manifest:

```json
{
  "delivery_id": "data_delivery_2026_05_19",
  "prepared_by": "data_analyst_name",
  "prepared_at": "2026-05-19T12:00:00Z",
  "files": [
    {
      "path": "past_questions/waec_mathematics_2024_paper_1.json",
      "file_type": "past_question_parse",
      "exam_type": "WAEC",
      "subject": "mathematics",
      "year": 2024,
      "status": "ready",
      "notes": ""
    }
  ]
}
```

## Validation Checklist

Before sending, confirm:

- Every JSON file opens without syntax errors.
- Every `topic` matches a canonical concept key.
- Every question has required RAG metadata.
- Every MCQ has exactly four options, `A` to `D`.
- Every worked solution is complete and does not invent missing steps.
- Every source PDF is included in `source_files/`.
- Any uncertainty is written in the manifest `notes`.
