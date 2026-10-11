# Synthetic long-context runtime integration test

This directory contains a small native llama.cpp integration test and its bounded Python driver. It tests this repository's software; it is not an inference service, scored task battery, or production application.

## Fixed input identities

- Runtime: ggml-org/llama.cpp commit `23b0202a189c44a54625aadcb37a946dd1d6278d`.
- Model: ggml-org/SmolLM3-3B-GGUF revision `4965cb60b150737b68a0408c36aeefb65078f894`.
- File: `SmolLM3-Q4_K_M.gguf`.
- Model SHA-256: `8334b850b7bd46238c16b0c550df2138f0889bf433809008cc17a8b05761863e`.
- Upstream reference: the pinned `include/llama.h` and `examples/simple/simple.cpp` APIs. No unpinned install script or provider inference API is used.

## Test

The native probe tokenizes generated ASCII records using the loaded GGUF vocabulary, selects exactly 49,152 content tokens, detokenizes them, and requires exact native re-tokenization equality. No automatic special tokens or chat wrapper are added. It allocates at least 53,248 context slots: 49,152 input plus 4,096 output reserve. It decodes every input token at consecutive positions, with no sliding window or context reduction implemented in the test, then greedily generates and decodes up to 16 output tokens.

Two separate native processes load the same model and repeat the identical full-context test. Input text, native token IDs, output text, and generated token IDs must have identical SHA-256 hashes. The full 4,096 output tokens are NOT generated in this minimal test; their capacity is reserved. Passing does not establish reasoning accuracy, long-context recall, or experiment readiness.

Record actual model-load/context-allocation times, prompt-processing and generation throughput, kernel peak RSS, sampled memory headroom/pressure/swap state, compiler/build logs, executable SHA-256, source hashes, OS and runner-image identity. The process time limit is 800 seconds per inference replica; the driver stops at 2,050 seconds overall, an outer timeout is 2,100 seconds, and the one job is limited to 40 minutes. A timeout is a measured bounded failure, not proof that a longer run could never work.

Initial headroom must be at least 10 GiB RAM and 6 GiB disk. Stop on less than 1 GiB available RAM, new swap-out, failed integrity or context checks, another active workflow, or peak native RSS of at least 13 GiB. No automatic retry, alternative checkpoint, smaller context, or paid hardware fallback is allowed.

## Execution and cost boundary

Use only the standard `ubuntu-24.04` GitHub-hosted public-repository runner, with four CPU threads and f16 K/V caches. The workflow grants no token permissions and uses anonymous public source/model downloads. No cache, artifact upload, package publication, external inference endpoint, or persistent service is used. Only synthetic source and bounded job logs are public.

GitHub documents standard public-repository runners as free; its Actions terms still require repository-related software testing and proportionate use:
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features

The workflow is initially staged without an automatic trigger. A separately recorded one-use request-file push may trigger the authorized qualification only after source identity and duplicate-run checks. Do not rerun, edit the request file, or expand this into continuing compute.
