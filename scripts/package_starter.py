"""Package the blank workspace and the filled synthetic practice example."""
from pathlib import Path
import argparse,json,re,zipfile

ROOT=Path(__file__).resolve().parents[1]
TEMPLATES=ROOT/'templates'
REPO='https://github.com/Rain-dust/HowToCompeteBetter/blob/main/'

def archive_bytes(path):
    raw=path.read_bytes()
    if path.suffix.lower()!='.md':return raw
    def replace(match):
        label,target=match.groups()
        if '://' in target or target.startswith('#'):return match.group(0)
        pure,sep,fragment=target.partition('#')
        resolved=(path.parent/pure).resolve()
        try:resolved.relative_to(TEMPLATES)
        except ValueError:
            target=REPO+resolved.relative_to(ROOT).as_posix()+(sep+fragment if sep else '')
        return '['+label+']('+target+')'
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',replace,raw.decode('utf8')).encode('utf8')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.parse_args()
    dirs=[TEMPLATES/'contest-starter',TEMPLATES/'contest-starter-example']
    files=sorted(p for d in dirs for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.suffix=='.pyc')
    output=TEMPLATES/'contest-starter.zip'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in files:
            info=zipfile.ZipInfo(path.relative_to(TEMPLATES).as_posix(),(2026,11,17,12,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            archive.writestr(info,archive_bytes(path))
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert 'contest-starter-example/run.py' in archive.namelist()
    print(json.dumps({'archive':'templates/contest-starter.zip','files':len(files),'bytes':output.stat().st_size}))

if __name__=='__main__':main()
