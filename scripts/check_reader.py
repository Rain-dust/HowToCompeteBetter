"""Check reader navigation, generated views, source contracts and the no-model example."""
from pathlib import Path
from urllib.parse import unquote
import argparse,ast,hashlib,json,re,shutil,subprocess,sys,tempfile,unicodedata,xml.etree.ElementTree as ET,zipfile

ROOT=Path(__file__).resolve().parents[1]

def headings(path):
    text=path.read_text('utf8');result=set();seen={}
    for heading in re.findall(r'^#{1,6}\s+(.+)$',text,re.M):
        heading=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',heading)
        base=''.join(c for c in heading.lower() if not unicodedata.category(c).startswith(('P','S')) or c in '-_').replace(' ','-')
        n=seen.get(base,0);seen[base]=n+1;result.add(base+('-'+str(n) if n else ''))
    result.update(re.findall(r'id="([^\"]+)"',text))
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pdf',action='store_true');args=parser.parse_args()
    rows=json.loads((ROOT/'data/competitions.json').read_text('utf8'))
    ranked=sorted((r for r in rows if isinstance(r.get('rank'),int)),key=lambda r:r['rank'])
    assert [r['rank'] for r in ranked]==list(range(1,28))
    assert len(rows)==len({r['id'] for r in rows})
    assert all(isinstance(r['playbook'],list) and isinstance(r['detail'],dict) for r in rows)
    assert all((ROOT/r['card_path']).is_file() for r in rows)
    assert len({r['card_path'] for r in ranked})==27
    math=next(r for r in rows if r['id']=='N22')
    assert '$1start-mathmodel' in math['detail']['prompt'] and '$mathmodel-skill' not in math['detail']['prompt']
    assert len(json.loads((ROOT/'data/social-feedback.json').read_text('utf8'))['records'])==75
    assert len(json.loads((ROOT/'data/feedback-records.json').read_text('utf8'))['external'])==22
    for script in ['build_catalog.py','build_readme.py','build_explorer.py']:
        subprocess.run([sys.executable,str(ROOT/'scripts'/script),'--check'],cwd=ROOT,check=True)
    for path in (ROOT/'scripts').glob('*.py'):ast.parse(path.read_text('utf8'))
    mdpaths=[ROOT/'README.md',ROOT/'CONTRIBUTING.md']+list((ROOT/'docs').rglob('*.md'))+list((ROOT/'templates').rglob('*.md'))+list((ROOT/'examples').rglob('*.md'))
    broken=[];links=0;anchors=0
    for path in mdpaths:
        text=path.read_text('utf8')
        for href in re.findall(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)',text)+re.findall(r'(?:href|src)="([^\"]+)"',text):
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',href):continue
            pure,sep,anchor=href.partition('#');pure=unquote(pure.split('?')[0]).strip('<>')
            target=(path.parent/pure).resolve() if pure else path
            links+=1
            if not target.exists():broken.append(str(path.relative_to(ROOT))+': '+href);continue
            if sep and target.suffix=='.md':
                anchors+=1
                if unquote(anchor) not in headings(target):broken.append(str(path.relative_to(ROOT))+': missing anchor '+href)
    assert not broken,'\n'.join(broken)
    for path in (ROOT/'assets').glob('*.svg'):ET.parse(path)
    html=(ROOT/'docs/explorer.html').read_text('utf8')
    assert not re.search(r'<script[^>]+src=',html,re.I),'Offline viewer must not require external scripts'
    assert 'releases/latest/download/explorer.html' in (ROOT/'README.md').read_text('utf8')
    with zipfile.ZipFile(ROOT/'templates/contest-starter.zip') as archive:
        assert archive.testzip() is None and 'contest-starter-example/run.py' in archive.namelist()
    temp_root=ROOT/'tmp';temp_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='reader-check-',dir=temp_root) as name:
        test=Path(name).resolve();assert test.is_relative_to(temp_root.resolve())
        dest=test/'practice';shutil.copytree(ROOT/'templates/contest-starter-example',dest,ignore=shutil.ignore_patterns('results','__pycache__'))
        subprocess.run([sys.executable,str(dest/'run.py')],cwd=test,check=True,capture_output=True)
        result=json.loads((dest/'results/summary.json').read_text('utf8'))
        assert (result['input_rows'],result['valid_rows'],result['rejected_rows'],result['total_minutes'],result['model_calls'])==(15,10,5,450,0)
        assert json.loads((dest/'results/checks.json').read_text('utf8'))['passed']
    # The numerical paper is unchanged; verify its immutable published hash, not another costly rerun.
    example=ROOT/'examples/cumcm2024b'
    summary=json.loads((example/'run-summary.json').read_text('utf8'))
    assert hashlib.sha256((example/'paper/main.pdf').read_bytes()).hexdigest()==summary['paper_sha256']
    pdf_result=None
    if args.pdf:
        from pypdf import PdfReader
        reader=PdfReader(ROOT/'guide.pdf');assert len(reader.pages)==30 and len(reader.outline)==30
        destinations=0;first=0
        for i,page in enumerate(reader.pages):
            for annotation in page.get('/Annots',[]):
                obj=annotation.get_object()
                if obj.get('/Subtype')=='/Link' and (obj.get('/Dest') or obj.get('/A',{}).get('/S')=='/GoTo'):
                    destinations+=1;first+=int(i==0)
        assert destinations>=40 and first>=4
        pdf_result={'pages':30,'bookmarks':30,'internal_links':destinations,'first_page_internal_links':first}
    print(json.dumps({'status':'passed','catalog':len(rows),'ranked':27,'markdown_files':len(mdpaths),'local_links':links,'anchors':anchors,'practice':'15/10/5 rows; 450 minutes; 0 model calls','pdf':pdf_result},ensure_ascii=False))

if __name__=='__main__':main()
