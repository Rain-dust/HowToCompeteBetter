"""Create a local MathModelAgent skills workspace. Does not call a model."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys,urllib.request,zipfile
from pathlib import Path
REPO='https://github.com/jihe520/MathModelAgent.git'
COMMIT='03f4eb388b3862b7bde55b508dceaf3d6b39d5ac'
SKILLS=['1start-mathmodel','2analysis-modeling','3coding-visual','4drawio','5writing','6verity','typst-author','mathmodel-figure-templates','_references']
PACKAGES=['numpy==2.5.5','scipy==1.18.1','pandas==3.1.1','matplotlib==3.11.2','pymupdf==2.1','pypdf==7.1.0','pillow==13.0.0','openpyxl==3.1.5']
def run(args):subprocess.run([str(a) for a in args],check=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--source',type=Path,help='Existing exact-commit upstream checkout; optional offline source');p.add_argument('--skip-env',action='store_true');p.add_argument('--typst',type=Path,help='Existing official typst executable');a=p.parse_args()
 w=a.workspace.resolve();w.mkdir(parents=True,exist_ok=True)
 marker=w/'workspace.json'
 if any(w.iterdir()) and not marker.exists():raise SystemExit('Refusing to overwrite a nonempty directory without workspace.json; select a new directory.')
 marker.write_text(json.dumps({'upstream':REPO,'commit':COMMIT,'setup_complete':False},indent=2),'utf8')
 if a.source:s=a.source.resolve()
 else:
  s=w/'third_party'/'MathModelAgent'
  if not s.exists():run(['git','clone',REPO,s])
  run(['git','-C',s,'checkout','--detach',COMMIT])
 actual=subprocess.check_output(['git','-C',str(s),'rev-parse','HEAD'],text=True).strip()
 if actual!=COMMIT:raise SystemExit('Upstream commit mismatch: '+actual)
 for client in ['.agents','.claude']:
  dest=w/client/'skills';dest.mkdir(parents=True,exist_ok=True)
  for name in SKILLS:
   target=dest/name
   if not target.exists():shutil.copytree(s/'skills'/name,target)
 shutil.copy2(s/'docs/md/License.md',w/'UPSTREAM-LICENSE.txt')
 (w/'inputs').mkdir(exist_ok=True)
 if not a.skip_env:
  uv=shutil.which('uv')
  if not uv:raise SystemExit('Install uv first, then rerun this command. See the tutorial; no global Python packages are changed.')
  v=w/'.venv';py=v/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
  if not py.exists():run([uv,'venv','--python','3.12',v])
  run([uv,'pip','install','--python',py,*PACKAGES])
  if os.name=='nt':shutil.copy2(py,v/'Scripts/python3.exe')
 typst=a.typst.resolve() if a.typst else (Path(shutil.which('typst')) if shutil.which('typst') else None)
 if typst is None:
  if os.name!='nt':raise SystemExit('Install official Typst and rerun with --typst /path/to/typst; automated compiler download is tested on Windows only.')
  tools=w/'.tools';tools.mkdir(exist_ok=True);archive=tools/'typst-0.15.1-windows.zip'
  if not archive.exists():
   req=urllib.request.Request('https://github.com/typst/typst/releases/download/v0.15.1/typst-x86_64-pc-windows-msvc.zip',headers={'User-Agent':'HowToCompeteBetter-Setup'})
   with urllib.request.urlopen(req,timeout=90) as response:archive.write_bytes(response.read())
  expected_hash='19ce3551153c2fe7ee9fa2f95208310c8f4d3209fedb699e0333faf8913f6736'
  actual_hash=hashlib.sha256(archive.read_bytes()).hexdigest()
  if actual_hash!=expected_hash:raise SystemExit('Typst archive hash mismatch; use the official release or --typst with a verified existing executable.')
  with zipfile.ZipFile(archive) as z:
   for name in z.namelist():
    if name.endswith('/typst.exe'):
     typst=tools/'typst.exe';typst.write_bytes(z.read(name));break
  if typst is None:raise SystemExit('Official archive has no typst.exe')
 version=subprocess.check_output([str(typst),'--version'],text=True).strip()
 result={'upstream':REPO,'commit':actual,'setup_complete':True,'typst':str(typst),'typst_version':version,'skills':SKILLS,'models_called':False,'license':'UPSTREAM-LICENSE.txt','tested_platform':'Windows 10 build 19045 / Python 3.12; other platforms not end-to-end tested'}
 marker.write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
 print('Setup complete. Add the actual problem PDF to inputs/problem.pdf. No model has been called.')
 print('Skills: $1start-mathmodel; reopen your coding-agent session in this workspace if necessary.')
if __name__=='__main__':main()
