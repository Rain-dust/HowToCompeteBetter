/** Verify generated website navigation, source counts, and all published bytes. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
execFileSync(process.execPath,[path.join(root,'scripts/build_site.mjs'),'--check'],{cwd:root,stdio:'inherit'});
const read=name=>fs.readFile(path.join(root,'_site',name),'utf8');
const data=JSON.parse(await read('content.json'));
const manifest=JSON.parse(await read('build-manifest.json'));
function assert(value,label){if(!value)throw Error(label);}
assert(data.chapters.length===10,'Ten chapters required');
assert(data.chapters.reduce((n,c)=>n+c.sections.length,0)===57,'Chapter sections differ');
const ranked=data.contests.filter(c=>c.rank).sort((a,b)=>a.rank-b.rank);
assert(JSON.stringify(ranked.map(c=>c.rank))===JSON.stringify(Array.from({length:27},(_,i)=>i+1)),'Ranking continuity differs');
assert(data.contests.length===73,'Contest entry count differs');
const index=await read('index.html');
const initialRanks=[...index.matchAll(/class="home-rank-item" data-rank="(\d+)"/g)].map(m=>+m[1]);
assert(JSON.stringify(initialRanks)==='[1,2,3,4,5]','First five ranks must render before the full book loads');
assert(index.includes('id="home-top5"')&&index.includes('id="home-rest-ranking"'),'Homepage ranking sections missing');
assert(!index.includes('<!-- HOME_RANK_PREVIEW -->'),'Ranking placeholder was not rendered');
for(const contest of ranked.slice(0,5)){
  assert(contest.homepage_tool_label,'Explicit homepage tool label required');
  assert(contest.top5_view?.start&&contest.top5_view?.github?.length,'Homepage launch task incomplete');
}
const chapters=new Map(data.chapters.map(c=>[c.id,c]));
const contests=new Map(data.contests.map(c=>[c.id,c]));
const pages=new Map(data.supplements.map(c=>[c.path,c]));
let links=0;
for(const record of [...data.chapters,...data.contests,...data.supplements]){
  for(const match of record.html.matchAll(/\b(?:href|src)="([^"]+)"/g)){
    const href=match[1].replace(/&amp;/g,'&');
    if(/^(https?:|mailto:|data:|\/\/)/.test(href))continue;
    links++;
    if(href.startsWith('#/')){
      const [route,query='']=href.slice(2).split('?');const parts=route.split('/').map(decodeURIComponent);
      let target,anchor;
      if(parts[0]==='chapter'){target=chapters.get(parts[1]);anchor=parts[2];}
      else if(parts[0]==='contest'){target=contests.get(parts[1]);anchor=parts[2];}
      else if(parts[0]==='page'){target=pages.get(parts.slice(1).join('/'));anchor=new URLSearchParams(query).get('section');}
      else {assert(['home','contests','search'].includes(parts[0]),'Unknown route '+href);continue;}
      assert(target,'Missing route '+href);
      if(anchor)assert([...target.html.matchAll(/\bid="([^"]+)"/g)].some(m=>m[1]===anchor),'Missing anchor '+href);
    }else{
      const filename=decodeURIComponent(href.split('#')[0].replace(/^\.\//,''));
      assert(manifest.files[filename],'Unpackaged file '+href);
    }
  }
}
for(const [name,expected] of Object.entries(manifest.files)){
  const bytes=await fs.readFile(path.join(root,'_site',name));
  assert(bytes.length===expected.bytes&&createHash('sha256').update(bytes).digest('hex')===expected.sha256,'Build bytes differ: '+name);
}
const pdf=await fs.readFile(path.join(root,'guide.pdf'));
assert(createHash('sha256').update(pdf).digest('hex')===manifest.files['guide.pdf'].sha256,'Website PDF must match published guide');
console.log(JSON.stringify({status:'passed',chapters:10,sections:57,contests:73,ranked:27,internalLinks:links,files:Object.keys(manifest.files).length,pdfMatched:true}));
