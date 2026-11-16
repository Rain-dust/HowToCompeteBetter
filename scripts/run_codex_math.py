"""Run the selected skill with existing Codex authentication; never reads API keys."""
from __future__ import annotations
import argparse,json,os,shutil,subprocess,time,uuid
from pathlib import Path
PROMPT='''使用 $1start-mathmodel 完整处理 inputs/problem.pdf 及其附件。从读题、建模、实际计算、图表、论文一路做到验收，不停在计划。偏好已经确定：Typst、国赛中文、子问题数按题面；不要重复询问已给偏好。按技能链依次执行，所有操作只在当前工作区。所有数字来自实算，不能伪造数据、参考文献或奖项；写明假设、近似与未解决项。最终完整重跑代码，实际编译 paper/main.pdf 并逐页渲染查看，发现问题修复后重验。交付源码、结果、图表、完整论文、验证报告及运行清单。Windows环境请明确使用cmd.exe或已安装Git Bash，避免把PowerShell转义原样套给cmd。'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--resume',help='Resume this existing Codex session ID in the same workspace');p.add_argument('--preflight',action='store_true',help='Check paths and CLI only; do not call a model');p.add_argument('--prompt-file',type=Path,help='Use a complete saved task instead of the generic starter');a=p.parse_args();w=a.workspace.resolve()
 config=json.loads((w/'workspace.json').read_text('utf8'))
 if not config.get('setup_complete'):raise SystemExit('Workspace setup is incomplete')
 py=w/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
 if not py.exists():raise SystemExit('Workspace Python missing; run setup without --skip-env')
 exe=shutil.which('codex.exe') or shutil.which('codex')
 if not exe:raise SystemExit('Codex CLI not found; install from official OpenAI documentation and sign in with codex login')
 env=os.environ.copy();env['PATH']=str(py.parent)+os.pathsep+str(Path(config['typst']).parent)+os.pathsep+env.get('PATH','');env['PYTHONUTF8']='1';env['MPLBACKEND']='Agg'
 subprocess.run([exe,'--version'],check=True,env=env,shell=False)
 subprocess.run([str(py),'-c','import numpy, scipy, pandas, matplotlib, fitz; print("Python stack OK")'],check=True,env=env)
 subprocess.run([config['typst'],'--version'],check=True,env=env)
 if a.preflight:print('Preflight passed; no model call.');return
 if not (w/'inputs/problem.pdf').is_file():raise SystemExit('Missing inputs/problem.pdf')
 logs=w/'run-logs'/(time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:12]);logs.mkdir(parents=True,exist_ok=False);prompt=a.prompt_file.read_text('utf8') if a.prompt_file else PROMPT
 print('Run logs:',logs,flush=True)
 meta={'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'driver':'Codex CLI','skill_commit':config['commit'],'approval':'workspace-write automatic review','result':'running'}
 (logs/'run.json').write_text(json.dumps(meta,indent=2),'utf8');(logs/'prompt.txt').write_text(prompt,'utf8')
 args=([exe,'exec','resume','--json','-o',str(logs/'last-message.txt'),a.resume,'-'] if a.resume else [exe,'exec','--approve-for-me','--json','-C',str(w),'-o',str(logs/'last-message.txt'),'-'])
 with (logs/'events.jsonl').open('w',encoding='utf8') as out,(logs/'stderr.log').open('w',encoding='utf8') as err:
  r=subprocess.run(args,input=prompt,text=True,encoding='utf8',stdout=out,stderr=err,env=env,cwd=str(w))
 meta.update(finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),exit_code=r.returncode,result='agent_finished' if r.returncode==0 else 'agent_error');(logs/'run.json').write_text(json.dumps(meta,indent=2),'utf8')
 print('Agent exited:',r.returncode,'Read reports/VERIFY_REPORT.md and inspect the produced PDF. A zero exit code is not an award or correctness certificate.')
 raise SystemExit(r.returncode)
if __name__=='__main__':main()
