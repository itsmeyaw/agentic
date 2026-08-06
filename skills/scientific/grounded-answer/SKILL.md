---
name: grounded-answer
description: Produces scientifically grounded answers by finding, evaluating, and clearly citing credible evidence. Use when users request scientific answers, research-backed explanations, studies, evidence, citations, or uncertainty-aware conclusions.
---

## Rule

- No statement is without citation or scientific background.
- Cited source should be a peer-reviewed scientific work.
- Prioritize recent scientific works.
- Prioritize high ranking journals, such as IEEE, ACM library. Arxiv is also a viable option.
- The scientific work must contain information of the statement, do not infer information based on the work title.
- Always read original file if you are unsure in the slightest.

## Tips

- Use the following MCPs and tools when available:
  - Webfetch
  - brave_search
  - consensus
  - paper-search
- Save downloaded file to a temporary directory (e.g., /tmp)
- When reading a pdf file, try first with `docling`. Command: `docling --to md --output <output_file_path> <input_file_path>`. It will generate a markdown file in the `<output_file_path>`.

## Format

- Answer in prose, unless asked otherwise.
- User numbered citation.
- In bibliography, attach only title, first author, DOI, and verbatim quote.

<example>
This is a statement [1]. This is a sentence that
do not require a citation.

[1] First Author. Title of work. DOI. "Verbatim quote"
</example>
