# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Automated pipeline that fetches password-encrypted credit card statement PDFs from Gmail (IMAP), unlocks them using the user's ID number as the password, parses transactions, and writes them to a Notion database. Runs on a GitHub Actions schedule (15th of each month, 18:00 Taiwan time).

## Commands

```bash
# Install dependencies
pip install pikepdf pdfplumber notion-client

# Run the pipeline (requires env vars)
python -m src.pipeline

# Run the full test suite (currently a single integration test script)
python tests/test_parse.py
```

## Environment variables required

| Variable | Purpose |
|---|---|
| `EMAIL_USER` | Gmail address |
| `EMAIL_PASS` | Gmail app password |
| `ID_NUMBER` | PDF unlock password (Taiwan ID number) |
| `NOTION_TOKEN` | Notion integration token |
| `NOTION_DATABASE_ID` | Target Notion database ID |

## Architecture

**Data flow:** Gmail (IMAP UNSEEN) → `pdf_unlock.py` (pikepdf) → parser → `NotionWriter` → mark email as seen

### Key design decisions

- **Idempotency via email flags**: emails are only marked `\Seen` after all Notion writes succeed. A partial failure keeps the email unseen so the next run retries it.
- **Parser dispatch by sender email**: `src/parsers/__init__.py` maps sender addresses to parser classes in `SENDER_MAP`. Add a new bank by adding an entry there and a new `BaseParser` subclass.
- **PDF passwords**: all statement PDFs are encrypted with the account holder's Taiwan ID number (`ID_NUMBER` env var), unlocked in-memory via `pikepdf` before passing to `pdfplumber`.

### Adding a new bank parser

1. Create `src/parsers/<bank>.py` subclassing `BaseParser` and implementing `parse(pdf) -> list[Transaction]`.
2. Add the sender email → parser class mapping to `SENDER_MAP` in `src/parsers/__init__.py`.
3. Hard-code the Notion payment page IDs (relation field) for each card inside the parser (see `esun.py` `UNICARD_PAGE_ID` or `sinopac.py` `CARD_MAP`).

### Notion database schema

The target database expects these properties:
- `名稱` (title) — transaction description
- `花費日期` (date) — spend date
- `金額` (number) — amount in TWD
- `支付方式` (relation) — links to a payment method page by its UUID
