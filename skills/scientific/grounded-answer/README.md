# Grounded Answer

Provide a scientific-backed answers for agent.

## Setup

Install and run the PDF conversion script with the same Python interpreter. Avoid
using `pip` on its own because it can target a different Python installation.

```sh
python3 -m pip install -r requirements.txt
python3 scripts/pdf-to-markdown.py --input paper.pdf --output paper.md
```

If you use `python` rather than `python3`, replace both commands consistently:

```sh
python -m pip install -r requirements.txt
python scripts/pdf-to-markdown.py --input paper.pdf --output paper.md
```

## Requirement

- MCP (each of them are optional, but each can improve the result):
  - [brave_search](https://brave.com/search/api/guides/use-with-claude-desktop-with-mcp/)
  - [consensus](https://docs.consensus.app/docs/mcp)
  - [paper-search-mcp](https://github.com/openags/paper-search-mcp)

- System:
  - Python3
  - [docling](https://pypi.org/project/docling/) (optional, installable using requirements.txt)
  - [pypdf](https://pypi.org/project/pypdf/) (optional, installable using requirements.txt)
