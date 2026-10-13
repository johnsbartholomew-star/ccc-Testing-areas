# CCC-2X V3 — Provider-backed evidence correction (2026-10-12)

**STATUS:** Non-destructive source-provenance correction. Original V3 workflow and historical artifacts remain intact. No model rerun occurred.

## Controlling source

- GitHub Actions repository: `johnsbartholomew-star/ccc-Testing-areas`
- V3 run `38126123294`, job `114430742945`, attempt 1, conclusion `completed/failure`.
- Executed commit `90073f96b464cb9ec0f1e5b86e55292db3bba469`.
- [Original provider run](https://github.com/johnsbartholomew-star/ccc-Testing-areas/actions/runs/38126123294).
- Full original provider job log copied into [`provider-job-114430742945-full.log`](./provider-job-114430742945-full.log), pinned at `e600a2ad7eacb8cf241331db6381842ebbe5ff01`, Git blob `6365d243f943b559067e831d59385cd0ededd046`, UTF-8 SHA-256 `81fe6f4625053e8d22a13022fc81d2f5f99cd3c4d7f56c84e2e43aca229fb392`, **392,136 bytes**.
- Corrected machine-readable extraction: [`provider-corrected-v3.json`](./provider-corrected-v3.json), Git blob `5838dba444b2d9e8a0cddd931b0bb1a944b6e45a`, commit `2b659b463e970557ec9c037cc8ef0dabe9fe1dba`.

## Original provider results versus later historical extraction

The historical `runtime-preflight/results/qualification-v3.json` was added at `0d5523cba9b6c00c73cb44421186677dc6987b58`, after the original provider job completed, and is not itself a provider-produced attachment.

| Property | Historical derived JSON | Provider original log |
|---|---|---|
| Last confirmed checkpoint | 24,576 tokens at 770.295319s | **16,384 at 693.725s** |
| Model GGUF bytes | 1,923,052,064 | **1,915,305,312** |
| Native executable SHA-256 | `d0506446…` | **`e53054a2…`** |
| Allocated CPU | AMD EPYC 7763 | **4 vCPUs / AMD EPYC 9V74** |
| OS | Ubuntu 24.04.3 LTS | **Ubuntu 24.04.5 LTS** |
| Runner image | 20261005.1 | **20261004.327.1** |
| Native process elapsed | 800.612973s | **800.971142368s** |
| Driver elapsed | 960.377194s | **898.509535271s** |
| Sampled VmHWM | 6,367,892 KiB | **7,108,828 KiB** |
| Source input.txt bytes | 200,554 | **196,622** |
| Source input.txt SHA-256 | `de52e53a…` | **`06d9401f…`** |

**Checks that survive correction:** same pinned GGUF revision and model SHA-256 `8334b850b7bd46238c16b0c550df2138f0889bf433809008cc17a8b05761863e`; exact 49,152 native tokenizer accounting; 53,248 allocated context slots (49,152 input + 4,096 output reserve); original source checksums; failed first native process at the 800-second predeclared limit; no generation; no fresh-process repeat.

**Source precedence:** the provider's terminal `PIN_VERIFICATION`, `INFERENCE_RECEIPT` and `FINAL_RESULT_JSON` records determine the original run's measured values. The original derived JSON, secondary native excerpt, and original private Manager return are kept immutable for the audit trail, but their contradictory measurements are superseded.

**Cause:** exact origin of the erroneous secondary extraction is UNKNOWN. Publication timing and inconsistent independent fields are verified; speculation about manual transcription, mixing, or substitution is not accepted as proof of cause. No alternate V3 attempt was located.

**Boundary:** This correction does not demonstrate long-context generation, fresh-process reproducibility, score any CCC-2X condition, change the frozen scientific specification, or authorize any new execution. Do not use the superseded V3 derived fields to claim or compare throughput.

## Reproduction

Read the pinned original provider log and independently parse the *last* `PIN_VERIFICATION`, `INFERENCE_RECEIPT`, and `FINAL_RESULT_JSON` records. Confirm run/commit identity, checksum, ordered 4,096-token checkpoints and the terminal timeout. The corrected JSON provides complete field-by-field comparisons, derived partial prefix throughput, measured resource pressure and provenance limitations.
