"""Resume public EDA/TEMP downloads; verify all before running the fixed probe."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'dataset/big_ideas_1_1_3'
HASHES = {r.split()[1]:r.split()[0] for r in (DATA/'SHA256SUMS.txt').read_text().splitlines()}
PATHS = [f'{p:03}/{m}_{p:03}.csv' for p in [2,4,5,6,7,8] for m in ['EDA','TEMP']]


def download(path):
    file = DATA/path
    for attempt in range(3):
        if file.exists() and hashlib.sha256(file.read_bytes()).hexdigest() == HASHES[path]:
            break
        url = 'https://physionet.org/files/big-ideas-glycemic-wearable/1.1.3/'+path
        # Timeout retries retain the partial file; never silently restart from byte zero.
        result = subprocess.run(['curl','-sS','-L','--fail','--continue-at','-',
                                 '--connect-timeout','30','--max-time','1800',url,'-o',str(file)])
        if result.returncode not in [0,28]:
            raise RuntimeError(f'{path}: curl exit {result.returncode}; partial file preserved')
    assert file.exists() and hashlib.sha256(file.read_bytes()).hexdigest()==HASHES[path], path
    row = dict(path=path, bytes=file.stat().st_size, sha256=HASHES[path])
    print('VERIFIED',path,row['bytes'],flush=True)
    return row


if __name__ == '__main__':
    results, errors = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download,p):p for p in PATHS}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                errors.append(dict(path=futures[future],error=str(exc)))
                print('ERROR',errors[-1],flush=True)
            (DATA/'skin_download_manifest.json').write_text(json.dumps(results,indent=2))
            (DATA/'skin_download_status.json').write_text(json.dumps(dict(verified=len(results),
                expected=len(PATHS),errors=errors),indent=2))
    if errors:
        raise SystemExit('Download errors; model was not started.')
    print('All input hashes verified; starting fixed model.',flush=True)
    subprocess.run([str(ROOT/'analysis/lipid_meals/.venv/bin/python'),'-u',
                    str(ROOT/'analysis/big_ideas_audit/skin_model.py')],check=True,cwd=ROOT)
