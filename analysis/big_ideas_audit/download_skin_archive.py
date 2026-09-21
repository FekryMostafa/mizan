"""Fetch only selected compressed ZIP entries, then verify publisher raw hashes."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'dataset/big_ideas_1_1_3'
URL = 'https://physionet.org/content/big-ideas-glycemic-wearable/get-zip/1.1.3/'
HASHES = {r.split()[1]:r.split()[0] for r in (DATA/'SHA256SUMS.txt').read_text().splitlines()}
ENTRIES = json.loads((ROOT/'reference/literature_refresh/skin_zip_inventory.json').read_text())


def get_range(offset,size):
    result = subprocess.check_output(['curl','-sS','--fail','--retry','2','--max-time','600',
        '--max-filesize',str(size),'--range',f'{offset}-{offset+size-1}',URL])
    assert len(result)==size
    return result


def download(entry):
    path = '/'.join(entry['name'].split('/')[-2:])
    assert path in HASHES and int(path[:3]) in [2,4,5,6,7,8]
    file = DATA/path
    if not file.exists() or hashlib.sha256(file.read_bytes()).hexdigest()!=HASHES[path]:
        header = get_range(entry['offset'],30)
        assert header[:4]==b'PK\x03\x04'
        assert struct.unpack_from('<H',header,8)[0]==8, 'Expected deflate'
        name_len, extra_len = struct.unpack_from('<HH',header,26)
        payload = get_range(entry['offset']+30+name_len+extra_len,entry['compressed'])
        raw = zlib.decompress(payload,-15)
        assert len(raw)==entry['size']
        assert hashlib.sha256(raw).hexdigest()==HASHES[path]
        temporary = file.with_suffix('.verified.tmp')
        temporary.write_bytes(raw)
        temporary.replace(file)
    print('VERIFIED',path,file.stat().st_size,flush=True)
    return dict(path=path,bytes=file.stat().st_size,sha256=HASHES[path],
                method='selected publisher ZIP entry; raw SHA256 verified')


if __name__=='__main__':
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(download,e) for e in ENTRIES]):
            results.append(future.result())
            (DATA/'skin_download_manifest.json').write_text(json.dumps(results,indent=2))
    assert len(results)==12
    (DATA/'skin_download_status.json').write_text(json.dumps(dict(verified=12,expected=12,errors=[])))
    print('All input hashes verified; starting fixed model.',flush=True)
    subprocess.run([str(ROOT/'analysis/lipid_meals/.venv/bin/python'),'-u',
                    str(ROOT/'analysis/big_ideas_audit/skin_model.py')],check=True,cwd=ROOT)
