# ADR-001: Local Chat Model Selection
**Date:** 2026-02-21
**Status:** Proposed

## Context
Filebrain needs a local LLM for RAG-powered Q&A over indexed files. The model runs
on an RTX 5070 Laptop GPU with 8GB VRAM, alongside nomic-embed-text (~274MB). The
model must be good at instruction following, source citation, and admitting uncertainty.

## Options Considered

### Option A: Qwen 2.5 7B (qwen2.5:7b)
- Pros: Excellent instruction following for its size, strong reasoning, good at
  structured output and citation tasks, ~4.7GB at Q4_K_M, leaves room for embedding
  model in VRAM simultaneously
- Cons: Qwen ecosystem less familiar to some users than Meta's

### Option B: Llama 3.1 8B (llama3.1:8b)
- Pros: Well-known, large community, strong general performance, good tool use
- Cons: Slightly larger (~4.9GB Q4_K_M), marginally less capable at structured
  instruction following than Qwen 2.5 in benchmarks

### Option C: Gemma 2 9B (gemma2:9b)
- Pros: Strong quality, good at following complex instructions
- Cons: ~5.4GB at Q4_K_M, tighter VRAM fit, slower inference due to larger size

### Option D: Mistral 7B v0.3 (mistral:7b)
- Pros: Fast inference, good general quality
- Cons: Weaker at instruction following compared to Qwen 2.5 and Llama 3.1,
  less capable at citation tasks

## Decision
**Qwen 2.5 7B** (`qwen2.5:7b`). It offers the best instruction following and
structured output quality at 7B scale, fits comfortably in 8GB VRAM alongside
the embedding model, and benchmarks well on the specific capabilities we need
(following citation format instructions, admitting when information is insufficient).

## Consequences
- Chat model pulled via `ollama pull qwen2.5:7b`
- Both models can coexist in VRAM (~274MB + ~4.7GB = ~5GB of 8GB)
- If quality is insufficient, Gemma 2 9B is the next candidate to try (tighter VRAM
  but potentially better quality)
- Easy to swap: only the model name in config needs to change. The RAG pipeline
  is model-agnostic.
- **Reversibility:** Easy — just pull a different model and change the config string
