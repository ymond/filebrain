# ADR-004: RAG Prompt Strategy
**Date:** 2026-02-22
**Status:** Accepted

## Context
The QueryEngine takes a user question, retrieves relevant file chunks via
semantic search, and asks the local LLM (qwen2.5:7b) to answer using those
chunks as context. The prompt must instruct the model to:
1. Answer based only on the provided context
2. Cite source files for every claim
3. Explicitly say when the context doesn't contain enough information

## Options Considered

### Option A: Simple context + question
```
Context: {chunks}
Question: {query}
Answer:
```
- Pros: Simple
- Cons: No citation instructions, model may hallucinate sources

### Option B: Structured prompt with explicit citation rules
```
You are a file search assistant. Answer questions based ONLY on the provided
file excerpts. For every claim, cite the source file path in [brackets].
If the excerpts don't contain enough information to answer, say so.

FILE EXCERPTS:
[path1]: chunk text...
[path2]: chunk text...

QUESTION: {query}
```
- Pros: Clear instructions, citation format defined, hallucination guard
- Cons: More tokens in the prompt

### Option C: JSON-structured output
- Pros: Machine-parseable citations
- Cons: More complex, qwen2.5:7b may not always produce valid JSON

## Decision
**Option B: Structured prompt with explicit citation rules.** Clear and reliable
with qwen2.5:7b. The citation format `[/path/to/file.ext]` is easy for users
to read and for code to verify against the metadata store.

The prompt template instructs the model to:
1. Only use information from provided excerpts
2. Cite sources as `[/path/to/file]` for every statement
3. Say "I don't have enough information" when context is insufficient
4. Never invent file paths

## Consequences
- Answers will contain inline file path citations
- We can verify citations against the metadata store (future enhancement)
- The prompt uses ~200 tokens of overhead per query
- Easy to iterate on the prompt without changing code (it's a string template)
- **Reversibility:** Easy — just change the prompt template string
