"""Build and publish static files to gh-pages without force-pushing history.

Uses the user's existing Git authentication. Enable GitHub Pages for gh-pages /
once in repository Settings > Pages; this script never prints or stores tokens.
"""
from pathlib import Path
import argparse,json,shutil,stat,subprocess,tempfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--git',default='git')
    parser.add_argument('--node',default='node')
    parser.add_argument('--skip-build',action='store_true')
    args=parser.parse_args()
    def git(*items,cwd=ROOT,check=True):
        return subprocess.run([args.git,*items],cwd=cwd,check=check,capture_output=True,text=True,encoding='utf8')
    if not args.skip_build:
        subprocess.run([args.node,str(ROOT/'scripts/build_site.mjs')],cwd=ROOT,check=True)
    subprocess.run([args.node,str(ROOT/'scripts/build_site.mjs'),'--check'],cwd=ROOT,check=True)
    output=(ROOT/'_site').resolve()
    manifest=json.loads((output/'build-manifest.json').read_text('utf8'))
    names=list(manifest['files'])+['build-manifest.json']
    for name in names:
        source=(output/name).resolve()
        if not source.is_relative_to(output) or not source.is_file():raise ValueError('Invalid build path')
    remote=git('remote','get-url','origin').stdout.strip()
    branch_exists=git('ls-remote','--exit-code',remote,'refs/heads/gh-pages',check=False).returncode==0
    parent=(ROOT/'tmp').resolve();parent.mkdir(exist_ok=True)
    checkout=Path(tempfile.mkdtemp(prefix='site-publish-',dir=parent)).resolve()
    if not checkout.is_relative_to(parent) or checkout==parent:raise ValueError('Unsafe checkout path')
    try:
        if branch_exists:git('clone','--config','core.autocrlf=false','--single-branch','--branch','gh-pages',remote,str(checkout))
        else:
            git('init','--initial-branch=gh-pages',cwd=checkout)
            git('remote','add','origin',remote,cwd=checkout)
        git('config','core.autocrlf','false',cwd=checkout)
        for key in ['user.name','user.email']:
            value=git('config',key).stdout.strip()
            if value:git('config',key,value,cwd=checkout)
        # The checked absolute checkout is an owned temporary directory. Remove
        # only files tracked in that deployment branch before copying the build.
        git('rm','-r','--ignore-unmatch','.',cwd=checkout)
        for name in names:
            dest=checkout/name;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(output/name,dest)
        git('add','--all',cwd=checkout)
        changed=git('diff','--cached','--quiet',cwd=checkout,check=False).returncode!=0
        if changed:
            git('commit','-m','Publish reading website '+manifest['version'],cwd=checkout)
            git('push','origin','HEAD:gh-pages',cwd=checkout)
        sha=git('rev-parse','HEAD',cwd=checkout).stdout.strip()
        print(json.dumps({'status':'published' if changed else 'unchanged','branch':'gh-pages','commit':sha,'url':'https://rain-dust.github.io/HowToCompeteBetter/','files':len(names)}))
    finally:
        def remove_readonly(function,name,_error):
            target=Path(name).resolve()
            if not target.is_relative_to(checkout):raise ValueError('Cleanup escaped temporary checkout')
            target.chmod(stat.S_IWRITE|stat.S_IREAD)
            function(name)
        if checkout.is_relative_to(parent) and checkout!=parent:
            shutil.rmtree(checkout,onerror=remove_readonly)

if __name__=='__main__':main()
