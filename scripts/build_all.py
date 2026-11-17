"""Rebuild reader views from one contest source; use --skip-pdf for text-only checks."""
from pathlib import Path
import argparse,shutil,subprocess,sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--skip-pdf',action='store_true');args=p.parse_args()
    for script in ['build_catalog.py','build_book.py','build_readme.py','build_explorer.py','package_starter.py']:
        subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,check=True)
    if not args.skip_pdf:
        subprocess.run([sys.executable,str(ROOT/'scripts/build_guide.py')],cwd=ROOT,check=True)
        path=ROOT/'output/pdf/高性价比大学生竞赛指南_v9_2026-11-17.pdf'
        shutil.copyfile(path,ROOT/'guide.pdf')
    print('Reader views rebuilt. Render and inspect the PDF and SVG assets before publishing.')

if __name__=='__main__':main()
