# CCC-2X V3 — Provider-backed evidence correction (October 12, 2026)

**Status: CORRECTION OF HISTORICAL DERIVED EVIDENCE, not a new qualification run.**

## Source priority

The canonical observation for V3 is the **original GitHub Actions provider job log** for run `38126123294`, job `114430742945`, executed commit `90073f96b464cb9ec0f1e5b86e55292db3bba469`, run attempt **1**.

- [Provider run](https://github.com/johnsbartholomew-star/ccc-Testing-areas/actions/runs/38126123294)
- Immutable full raw log: `provider-job-114430742945-full.log` at commit `e600a2ad7eacb8cf241331db6381842ebbe5ff01`, blob `6365d243f943b559067e831d59385cd0ededd046`, UTF-8 SHA-256 `81fe6f4625053e8d22a13022fc81d2f5f99cd3c4d7f56c84e2e43aca229fb392`, 392,136 bytes.
- Corrected structured extraction: `provider-corrected-v3.json` (see its own pinned Git commit and hash from this correction's publication).

## Material discrepancies

The earlier `runtime-preflight/results/qualification-v3.json` and its annotated excerpt were committed *after* the original job ended. Their descriptions of this same run conflict with the original provider log. The earlier derived JSON remains **unmodified** at commit `3871f628c42b3df4156d67c63551522f4d87d058`, blob `7bd686bdff9e027d292bfec61861efc901403764`.

| Measurement | Historical derived V3 | Original provider V3 |
|---|---|---|
| Last confirmed native input checkpoint | 24,576 tokens / 770.295319 s | **16,384 tokens / 693.725 s** |
| Model file bytes | 1,923,052,064 | **1,915,305,312** |
| Native executable SHA-256 | `d0506446…` | **`e53054a2…`** |
| CPU model | AMD EPYC 7763 | **AMD EPYC 9V74** |
| Ubuntu | 24.04.3 | **24.04.5** |
| Runner image version | 20261005.1 | **20261004.327.1** |
| Native process elapsed | 800.612973 s | **800.971142 s** |
| Driver elapsed | 960.377194 s | **898.509535 s** |
| Sampled native process peak VmHWM | 6,367,892 KiB | **7,108,828 KiB** |

**Agreements:** both cite the same model SHA-256 `8334b850b7bd46238c16b0c550df2138f0889bf433809008cc17a8b05761863e`, pinned llama.cpp commit `23b0202a189c44a54625aadcb37a946dd1d6278d`, 49,152-token native input, 4,096-slot reserve, 53,248 context allocation, checksum PASS, and the first-process timeout classification. Those shared identity claims do **not** validate conflicting measurements.

**Source-backed observed outcome:** first native process timed out after 800.971142 s, having last logged **16,384 of 49,152** input tokens. Its observed partial average was 23.6174 tokens/s through that checkpoint, not a completed 49k throughput measurement. Model integrity and native tokenizer round-trip passed; context allocation passed. Full prefill, generation, and independent fresh-process reproduction were **not** reached. Peak sampled VmHWM **7,108,828 KiB** (~6.78 GiB), no observed swap-out or memory-pressure stop. Native load API **1.2593 s**, not a cold-resident load benchmark.

## Cause investigation — unresolved

The workflow's executed revision does not publish the later derived JSON; the source-run and derivative-publication commits are distinct. Provider data contains **no** V3 checkpoint at 20,480 or 24,576, and there is just one recorded V3 attempt. The later derivative differs in hardware, model bytes, binary hash, and timings simultaneously. It might involve reconstruction/transcription error or mixing a different execution's data, **but the extraction's exact authoring inputs/lineage are not recovered**. Do not claim a definitive mechanism.

**Policy:** For V3 performance, memory, hardware, binary identity or model size, use the original provider log and this correction. Treat the historical derived file and historical private Manager return (`Claras-house@72a8f20c2ebd98bf2f47bda52c3ddcb7fae335ed`) as contradicted for these values. Preserve both for audit rather than rewriting history. V4 is a separate run on a different reported CPU host; don't interpret naive V3/V4 speed ratios as controlled hardware comparisons.

No model run, scored experiment, retry, production mutation, or paid compute occurred in this correction.
