"""Shared I/O only. All paths remain inside the project."""
from pathlib import Path
import json, sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def init():
    sys.stdout.reconfigure(encoding='utf-8')
    for d in ['results','figures','reports','paper/sections']:
        (ROOT/d).mkdir(parents=True,exist_ok=True)
def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))
def save(path,data):
    (ROOT/path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def csv(path,rows):
    pd.DataFrame(rows).to_csv(ROOT/path,index=False,encoding='utf-8-sig',float_format='%.12g')
