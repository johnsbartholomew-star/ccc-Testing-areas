# Synthetic runtime preflight V4 — time-only continuation

This software integration test continues V3 with **one** authorized run. Model checkpoint, model revision, native llama.cpp commit, synthetic input bytes/generation controls, runtime context, KV cache, CPU threads, memory guards, binary build, and runner class are unchanged. The V3 source and evidence remain untouched.

## Time-bounded variation only

- Native inference process limit: **3,600 seconds per fresh process**, increased from 800.
- Driver wall-time guard: **7,700 seconds**, increased from 2,050 to allow two bounded runs and setup.
- Workflow shell outer timeout: **7,800 seconds**, increased from 2,100.
- Standard runner job hard timeout: **135 minutes** (8,100 seconds), increased from 40 minutes.
- If fewer than 3,600 seconds remain in the driver budget before the second process, do not start it; report `REPRODUCIBILITY_NOT_ESTABLISHED`.
- One push-triggered request `requests/qualification-v4.json` and one job attempt only; no schedule, broad push, pull-request, workflow_dispatch, or retries.

## Frozen inputs

- `ggml-org/llama.cpp@23b0202a189c44a54625aadcb37a946dd1d6278d`
- `ggml-org/SmolLM3-3B-GGUF@4965cb60b150737b68a0408c36aeefb65078f894`
- `SmolLM3-Q4_K_M.gguf` SHA-256 `8334b850b7bd46238c16b0c550df2138f0889bf433809008cc17a8b05761863e`
- 49,152 model-native content tokens + 4,096 generation-reserve slots = 53,248 allocated context slots; up to 16 greedily decoded output tokens, not 4,096 actual generated tokens.
- `ubuntu-24.04` GitHub **standard public** hosted runner only. No larger runner, paid API, cache, artifact upload, or new credentials.
- `runtime-preflight/probe.cpp`, `CMakeLists.txt`, and synthetic input-generation source are **identical** to V3.

Source integrity gate: `sha256sum --check runtime-preflight/SHA256SUMS-v4`. Results appear in the bounded provider job log and private Manager receipt. V3 is not overwritten. No CCC-2X scored experiment or full harness build.

## Public terms

One bounded repository-local synthetic software integration test, not a generic hosted inference service. GitHub docs: https://docs.github.com/en/billing/concepts/product-billing/github-actions and https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features .
