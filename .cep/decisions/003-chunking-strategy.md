# ADR-003: Text Chunking Strategy
**Date:** 2026-02-22
**Status:** Accepted

## Context
Extracted text from files must be split into chunks before embedding. The embedding
model (nomic-embed-text) has a context window of 8192 tokens (~6000 words), but
embedding quality degrades on very long inputs. Chunks should be small enough for
focused semantic meaning but large enough for context.

## Options Considered

### Option A: Fixed-size character chunks with overlap
- Pros: Simple, predictable chunk sizes, overlap prevents information loss at boundaries
- Cons: May split mid-sentence or mid-word, less semantically coherent

### Option B: Sentence-aware chunks with overlap
- Pros: Respects sentence boundaries, more semantically coherent chunks, overlap
  captures context across chunk boundaries
- Cons: Slightly more complex, chunks may vary in size

### Option C: Recursive/semantic splitting (e.g. LangChain-style)
- Pros: Tries paragraphs first, then sentences, then characters
- Cons: Over-engineered for our needs, adds complexity without clear benefit at
  this stage, requires a heavy dependency

## Decision
**Sentence-aware chunks with overlap (Option B).** Target chunk size of ~1000
characters with ~200 character overlap. Split on sentence boundaries (period, question
mark, exclamation mark followed by whitespace) when possible, falling back to
character boundary when a single sentence exceeds the target size.

Parameters:
- `chunk_size`: 1000 characters (default)
- `chunk_overlap`: 200 characters (default)
- Sentence boundary detection: split on `. `, `? `, `! `, `.\n`, `?\n`, `!\n`

These defaults work well for nomic-embed-text which performs best on passages of
~100-500 tokens (~400-2000 characters). The 1000-char target with 200-char overlap
provides good semantic coherence while keeping chunks focused.

## Consequences
- Chunks are variable-length (bounded by chunk_size, may be shorter near sentence
  boundaries)
- Overlap means some text appears in multiple embeddings, improving retrieval at
  chunk boundaries at the cost of slightly more storage
- Short texts (below chunk_size) pass through as a single chunk — no splitting needed
- The chunker is a pure function with no dependencies beyond the standard library
- **Reversibility:** Easy — chunking parameters can be changed and files re-processed
