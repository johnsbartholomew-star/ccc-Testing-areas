# CCC-2X runtime-preflight results — evidence precedence (October 12, 2026)

## V3: original derived publication contains **CONTRADICTED MEASUREMENTS**

The historical `qualification-v3.json` and `qualification-v3-native-stage-excerpt.log` are deliberately retained unmodified for audit. **Do not use their throughput, host, model-byte, compiled-binary, memory or time measurements as facts about V3 run 38126123294.**

The original provider run #38126123294 / job #114430742945 confirms only **16,384 input tokens at 693.725 seconds** before an 800.971-second native timeout, not the later derivative's 24,576 at 770.295 seconds. The model SHA-256 and 53,248 context allocation are valid, but full input, generation and fresh-process reproduction were not reached. The cause of the discrepant derivative is UNKNOWN.

**Authoritative corrective evidence:** [full original provider log](./qualification-v3-provider-correction-2026-10-12/provider-job-114430742945-full.log), [provider-backed corrected V3 JSON](./qualification-v3-provider-correction-2026-10-12/provider-corrected-v3.json) and [correction explanation](./qualification-v3-provider-correction-2026-10-12/README_CORRECTION.md).

Original provider-log preservation commit: `e600a2ad7eacb8cf241331db6381842ebbe5ff01`; corrected extraction commit: `2b659b463e970557ec9c037cc8ef0dabe9fe1dba`. V3 was **not rerun**.

## V4: independent timed qualification result

V4 [full job log](./qualification-v4/github-actions-job-115028344812-full.log) and [terminal measurements](./qualification-v4/terminal-measurements.json) document run 38314672710, job 115028344812, which reached 45,056/49,152 input tokens at 3,505.41 seconds before the first process stopped at its 3,600-second cap. Generation and fresh-process repeat did not occur. V4 was a different VM host; V3-to-V4 raw speed ratios are not controlled CPU benchmarks.

Only read-only/source-evidence correction has been undertaken. No CCC-2X memory-leverage hypothesis was scored.
