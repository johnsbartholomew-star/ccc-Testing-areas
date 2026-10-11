#!/usr/bin/env python3
"""One public-runner integration test. Never an inference endpoint or experiment."""
from __future__ import annotations
import hashlib, json, os, pathlib, platform, signal, shutil, subprocess, sys, time, urllib.request

REPO = 'johnsbartholomew-star/ccc-Testing-areas'
LLAMA = '23b0202a189c44a54625aadcb37a946dd1d6278d'
MODEL_REV = '4965cb60b150737b68a0408c36aeefb65078f894'
MODEL_HASH = '8334b850b7bd46238c16b0c550df2138f0889bf433809008cc17a8b05761863e'
MODEL_URL = f'https://huggingface.co/ggml-org/SmolLM3-3B-GGUF/resolve/{MODEL_REV}/SmolLM3-Q4_K_M.gguf'
ROOT = pathlib.Path(__file__).resolve().parent
WORK = pathlib.Path.cwd() / '.runtime-preflight-work'
REPORT: dict = {'status': 'NOT_EXECUTED', 'model_revision': MODEL_REV, 'model_sha256': MODEL_HASH,
                'llama_commit': LLAMA, 'input_tokens': 49152, 'generation_reserve': 4096,
                'context_tokens': 53248, 'decoding': 'greedy; no RNG', 'max_generated_tokens': 16,
                'kv_cache': 'f16 K and V', 'scored_experiment': False, 'runs': []}
START = time.monotonic()

def sha(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def emit(name: str, value) -> None:
    print(name + ' ' + json.dumps(value, sort_keys=True, ensure_ascii=True), flush=True)

def require(ok: bool, msg: str) -> None:
    if not ok: raise RuntimeError(msg)

def metrics(pid: int | None = None) -> dict:
    mem = {line.split(':')[0]: int(line.split()[1]) for line in pathlib.Path('/proc/meminfo').read_text().splitlines()}
    vm = dict(line.split() for line in pathlib.Path('/proc/vmstat').read_text().splitlines())
    out = {'available_kib': mem['MemAvailable'], 'total_kib': mem['MemTotal'],
           'swap_used_kib': mem['SwapTotal'] - mem['SwapFree'], 'pswpout': int(vm['pswpout'])}
    psi = pathlib.Path('/proc/pressure/memory')
    out['memory_pressure'] = psi.read_text().strip() if psi.exists() else 'UNAVAILABLE'
    if pid:
        try:
            for line in pathlib.Path(f'/proc/{pid}/status').read_text().splitlines():
                if line.startswith(('VmRSS:', 'VmHWM:')): out[line.split(':')[0]] = int(line.split()[1])
        except FileNotFoundError: pass
    return out

def terminate(p: subprocess.Popen) -> None:
    if p.poll() is None:
        os.killpg(p.pid, signal.SIGTERM)
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL); p.wait()

def command(args: list[str], name: str, limit: int, cwd: pathlib.Path | None = None) -> tuple[int, str, dict]:
    """Bound time and memory, preserve logs even on an unsuccessful stage."""
    path = WORK / (name + '.log'); before = metrics(); minimum = before['available_kib']; peak = 0
    started = time.monotonic(); stop = None; latest = before
    with path.open('wb') as log:
        p = subprocess.Popen(args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            while p.poll() is None:
                latest = metrics(p.pid); minimum = min(minimum, latest['available_kib']); peak = max(peak, latest.get('VmHWM', 0))
                if time.monotonic() - started > limit: stop = 'STAGE_TIMEOUT'
                elif time.monotonic() - START > 2050: stop = 'TOTAL_TIME_LIMIT'
                elif latest['available_kib'] < 1024 * 1024: stop = 'MEMORY_HEADROOM_BELOW_1_GIB'
                elif latest['pswpout'] > before['pswpout']: stop = 'NEW_SWAP_OUT'
                if stop: terminate(p); break
                time.sleep(1)
        finally: terminate(p)
    elapsed = time.monotonic() - started; text = path.read_text(errors='replace')
    # Only this test's own stdout/stderr; never print the environment or credentials.
    print(f'BEGIN_LOG {name}', flush=True); print(text, end='\n', flush=True); print(f'END_LOG {name}', flush=True)
    measurement = {'stage': name, 'elapsed_seconds': elapsed, 'returncode': p.returncode, 'stop': stop,
                   'peak_observed_vm_hwm_kib': peak, 'minimum_available_kib': minimum,
                   'before': before, 'last_sample': latest, 'after': metrics(), 'log_sha256': sha(path)}
    REPORT.setdefault('stages', []).append(measurement); emit('STAGE_MEASUREMENT', measurement)
    return p.returncode if not stop else 124, text, measurement

def checked(args: list[str], name: str, limit: int, cwd: pathlib.Path | None = None) -> str:
    rc, text, _ = command(args, name, limit, cwd); require(rc == 0, name + '_FAILED'); return text

def main() -> None:
    require(os.environ.get('GITHUB_ACTIONS') == 'true', 'GITHUB_ACTIONS_REQUIRED')
    require(os.environ.get('GITHUB_REPOSITORY') == REPO, 'WRONG_REPOSITORY')
    require(os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted', 'STANDARD_HOSTED_RUNNER_REQUIRED')
    require(os.environ.get('RUNNER_OS') == 'Linux' and platform.machine() == 'x86_64', 'LINUX_X64_REQUIRED')
    require(os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'NO_AUTOMATIC_OR_MANUAL_RERUN')
    req = urllib.request.Request(f'https://api.github.com/repos/{REPO}', headers={'User-Agent': 'synthetic-runtime-preflight'})
    with urllib.request.urlopen(req, timeout=20) as r: repository = json.load(r)
    require(repository['private'] is False and repository['visibility'] == 'public', 'PUBLIC_VISIBILITY_REQUIRED')
    event = json.loads(pathlib.Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    require(event.get('repository', {}).get('private') is False, 'PUBLIC_EVENT_REQUIRED')
    WORK.mkdir(exist_ok=False)
    before = metrics()
    REPORT['runner'] = {'repository_id': repository['id'], 'public': True, 'platform': platform.platform(),
        'cpu_count': os.cpu_count(), 'os_release': pathlib.Path('/etc/os-release').read_text(),
        'cpuinfo': next((l for l in pathlib.Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('model name')), ''),
        'disk_free_bytes': shutil.disk_usage(WORK).free, 'memory': before,
        'identity': {k: os.environ.get(k) for k in ('ImageOS', 'ImageVersion', 'RUNNER_OS', 'RUNNER_ARCH', 'RUNNER_ENVIRONMENT', 'GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT')}}
    REPORT['source_files'] = {p.name: sha(p) for p in (ROOT / 'probe.cpp', ROOT / 'CMakeLists.txt', ROOT / 'qualify.py')}
    emit('RUNTIME_MANIFEST', REPORT)
    require(before['available_kib'] >= 10 * 1024 * 1024, 'INITIAL_MEMORY_BELOW_10_GIB')
    require(shutil.disk_usage(WORK).free >= 6 * 1024**3, 'DISK_BELOW_6_GIB')
    req = urllib.request.Request(f'https://api.github.com/repos/{REPO}/actions/runs?per_page=30', headers={'User-Agent': 'synthetic-runtime-preflight'})
    with urllib.request.urlopen(req, timeout=20) as r: runs = json.load(r)['workflow_runs']
    active = [r['id'] for r in runs if r['status'] in ('queued', 'in_progress', 'waiting', 'pending', 'requested') and str(r['id']) != os.environ['GITHUB_RUN_ID']]
    REPORT['other_active_runs'] = active; require(not active, 'COMPETING_WORKFLOW_DETECTED')
    src = WORK / 'llama.cpp'; src.mkdir()
    checked(['git', 'init', '--quiet'], 'git_init', 20, src)
    checked(['git', 'remote', 'add', 'origin', 'https://github.com/ggml-org/llama.cpp.git'], 'git_remote', 20, src)
    checked(['git', 'fetch', '--quiet', '--depth=1', 'origin', LLAMA], 'source_fetch', 120, src)
    checked(['git', 'checkout', '--quiet', '--detach', 'FETCH_HEAD'], 'source_checkout', 20, src)
    require(checked(['git', 'rev-parse', 'HEAD'], 'source_identity', 20, src).strip() == LLAMA, 'RUNTIME_REVISION_MISMATCH')
    REPORT['upstream_files'] = {p: sha(src / p) for p in ('include/llama.h', 'examples/simple/simple.cpp', 'CMakeLists.txt')}
    build = WORK / 'build'
    checked(['cmake', '-S', str(ROOT), '-B', str(build), f'-DLLAMA_SOURCE={src}', '-DCMAKE_BUILD_TYPE=Release',
        '-DBUILD_SHARED_LIBS=OFF', '-DLLAMA_BUILD_TESTS=OFF', '-DLLAMA_BUILD_EXAMPLES=OFF', '-DLLAMA_BUILD_SERVER=OFF',
        '-DLLAMA_BUILD_COMMON=OFF', '-DGGML_CUDA=OFF', '-DGGML_METAL=OFF', '-DGGML_VULKAN=OFF', '-DGGML_RPC=OFF',
        '-DGGML_NATIVE=ON', '-DGGML_OPENMP=ON', '-DGGML_BLAS=OFF'], 'configure', 120)
    checked(['cmake', '--build', str(build), '--target', 'runtime-probe', '--parallel', '4'], 'compile', 420)
    binary = build / 'runtime-probe'; require(binary.is_file(), 'EXECUTABLE_MISSING')
    REPORT['binary_sha256'] = sha(binary); REPORT['cmake_cache_sha256'] = sha(build / 'CMakeCache.txt')
    model = WORK / 'SmolLM3-Q4_K_M.gguf'
    checked(['curl', '--fail', '--location', '--silent', '--show-error', '--connect-timeout', '20', '--max-time', '300',
             '--max-filesize', '2147483648', '--output', str(model), MODEL_URL], 'model_download', 310)
    REPORT['model_bytes'] = model.stat().st_size; REPORT['observed_model_sha256'] = sha(model)
    require(REPORT['observed_model_sha256'] == MODEL_HASH, 'MODEL_HASH_MISMATCH')
    with model.open('rb') as f: require(f.read(4) == b'GGUF', 'INVALID_GGUF')
    prompt = WORK / 'synthetic.txt'
    prompt.write_text('Synthetic record stream for a software context-capacity test.\n' + ''.join(
        f'record {i:06d}: amber blue green silver.\n' for i in range(10000)), encoding='ascii')
    REPORT['synthetic_source_sha256'] = sha(prompt); emit('PIN_VERIFICATION', REPORT)
    for i in (1, 2):
        prefix = WORK / f'run{i}'
        rc, text, measurement = command([str(binary), str(model), str(prompt), str(prefix)], f'inference_{i}', 800)
        events = [json.loads(l) for l in text.splitlines() if l.startswith('{"stage":')]
        run = {'events': events, 'measurement': measurement, 'files': {}}
        for suffix in ('input.txt', 'input.tokens', 'output.txt', 'output.tokens'):
            p = pathlib.Path(str(prefix) + '.' + suffix)
            if p.exists(): run['files'][suffix] = {'sha256': sha(p), 'bytes': p.stat().st_size}
        output = pathlib.Path(str(prefix) + '.output.tokens')
        if output.exists(): run['output_token_ids'] = [int(x) for x in output.read_text().splitlines()]
        REPORT['runs'].append(run); emit('INFERENCE_RECEIPT', run)
        require(rc == 0 and events and events[-1].get('status') == 'PASS', f'INFERENCE_{i}_FAILED')
        result = events[-1]; require(result['processed_input_tokens'] == 49152, 'INCOMPLETE_CONTEXT_PROCESSING')
        require(result['peak_rss_kib'] < 13 * 1024 * 1024, 'MEMORY_PEAK_ABOVE_BOUND')
        context = next(x for x in events if x['stage'] == 'tokenizer_and_context')
        require(context['runtime_context'] >= 53248 and context['roundtrip_equal'], 'CONTEXT_OR_TOKENIZER_FAILED')
    a, b = REPORT['runs']
    same = all(a['files'][s]['sha256'] == b['files'][s]['sha256'] for s in ('input.txt', 'input.tokens', 'output.txt', 'output.tokens'))
    REPORT['fresh_process_reproduction'] = same; require(same, 'FRESH_PROCESS_OUTPUT_MISMATCH')
    REPORT['status'] = 'QUALIFIED_NON_SCORED_RUNTIME_ONLY'
    REPORT['generation_overhead_test'] = '4096 slots reserved; up to 16 output tokens decoded, not 4096 generated'
    REPORT['not_proven'] = ['semantic accuracy', 'long-context recall', 'scored experiment readiness', 'retrieval qualification']

if __name__ == '__main__':
    try: main()
    except Exception as exc:
        REPORT['status'] = 'FAILED_OR_BLOCKED'; REPORT['blocker'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        REPORT['total_elapsed_seconds'] = time.monotonic() - START
        emit('FINAL_RESULT_JSON', REPORT)
    sys.exit(0 if REPORT['status'] == 'QUALIFIED_NON_SCORED_RUNTIME_ONLY' else 1)
