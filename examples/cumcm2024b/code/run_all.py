"""Reproduce all four questions, independent validation, figures, and reports.

No package installation, credential access, external writes or network requests.
Invoke from cmd.exe: python.exe code\run_all.py
"""
from pathlib import Path
import subprocess,sys,time,json,os,platform,importlib.metadata,shutil
R=Path(__file__).resolve().parents[1]
def main():
    sys.stdout.reconfigure(encoding='utf-8');records=[]
    (R/'reports').mkdir(exist_ok=True)
    typst=shutil.which('typst')
    typst_version=subprocess.check_output([typst,'--version'],text=True).strip() if typst else 'Typst not on PATH during this numerical rerun; original PDF used 0.15.1'
    metadata={'python':platform.python_version(),'platform':platform.platform(),'typst_version':typst_version,'packages':{n:importlib.metadata.version(n) for n in ['numpy','scipy','pandas','matplotlib','PyMuPDF','pypdf','Pillow']},'scope':'Automatically collected for the public numerical rerun; no credential or private path fields'}
    (R/'reports/environment.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    env=os.environ.copy();env['PYTHONUTF8']='1';env['PYTHONIOENCODING']='utf-8'
    for script in ['code/problem1.py','code/problem2.py','code/problem3.py','code/problem4.py',
                   'code/validate_calculations.py','code/sensitivity.py','code/make_figures.py','code/write_results_report.py']:
        t=time.perf_counter()
        p=subprocess.run([sys.executable,script],cwd=R,env=env,capture_output=True,text=True,encoding='utf-8')
        records.append({'command':[sys.executable,script],'returncode':p.returncode,'seconds':time.perf_counter()-t,
                        'stdout':p.stdout,'stderr':p.stderr})
        print(script,':',p.returncode,flush=True)
        if p.returncode:
            (R/'reports/run_all_log.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
            print(p.stdout,p.stderr);raise SystemExit(p.returncode)
    (R/'reports/run_all_log.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print('All four questions and independent checks reproduced successfully.')
if __name__=='__main__':main()
