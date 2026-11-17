/** Build the GitHub Pages reading edition. Node 18+; no npm install required. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {marked} from './vendor/marked.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.join(root,'_site');
const repo='https://github.com/Rain-dust/HowToCompeteBetter';
const siteURL='https://rain-dust.github.io/HowToCompeteBetter/';
const read=relative=>fs.readFile(path.join(root,relative),'utf8');
const chapters=JSON.parse(await read('data/chapters.json'));
const contests=JSON.parse(await read('data/competitions.json'));
const chapterByFile=new Map(chapters.map(c=>[c.file,c]));
const contestByFile=new Map(contests.map(c=>[c.card_path,c]));
const copyFiles=new Set(['guide.pdf','templates/contest-starter.zip']);
const supplements=[];
const knownSupplements=new Set();
const args=new Set(process.argv.slice(2));
const manifest={version:'0.6.1',source:'book/ + data/competitions.json + maintained documents',files:{}};
const ent=text=>text.replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'");
const attribute=text=>text.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
const plain=html=>ent(html.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ')).trim();
function slug(text){return plain(text).toLowerCase().replace(/[\p{P}\p{S}]/gu,c=>c==='-'||c==='_'?c:'').replace(/ /g,'-');}
function allowed(relative){return !relative.startsWith('../')&&!path.posix.isAbsolute(relative)&&!/^(research|tmp|output|_site|\.git|\.agents|\.codex)(\/|$)/.test(relative)&&!relative.split('/').some(p=>p.startsWith('.'));}
function route(relative,anchor=''){
  const tail=anchor?'/'+encodeURIComponent(anchor):'';
  if(chapterByFile.has(relative))return '#/chapter/'+chapterByFile.get(relative).id+tail;
  if(contestByFile.has(relative))return '#/contest/'+contestByFile.get(relative).id+tail;
  if(relative==='README.md'||relative==='book/README.md')return '#/home';
  return '#/page/'+encodeURIComponent(relative)+(anchor?'?section='+encodeURIComponent(anchor):'');
}
function target(href,source){
  href=ent(href);
  if(!href||href.startsWith('mailto:')||href.startsWith('data:'))return href;
  if(href.startsWith(repo+'/blob/main/'))href='/'+href.slice((repo+'/blob/main/').length);
  if(href.startsWith(repo+'/raw/refs/heads/main/'))href='/'+href.slice((repo+'/raw/refs/heads/main/').length);
  if(/^(https?:)?\/\//.test(href))return href;
  if(/^[a-z][a-z0-9+.-]*:/i.test(href))return '#/home';
  const [pure,anchorRaw='']=href.split('#');
  let anchor;try{anchor=decodeURIComponent(anchorRaw);}catch{anchor=anchorRaw;}
  let decoded;try{decoded=decodeURIComponent(pure.split('?')[0]);}catch{decoded=pure.split('?')[0];}
  const relative=!decoded?source:path.posix.normalize(decoded.startsWith('/')?decoded.slice(1):path.posix.join(path.posix.dirname(source),decoded));
  if(!allowed(relative))return repo+'/blob/main/'+relative;
  if(relative.endsWith('.md'))return route(relative,anchor);
  if(/\.(pdf|zip|svg|png|jpg|jpeg|webp|json|csv|txt|py|typ|drawio)$/i.test(relative)){copyFiles.add(relative);return './'+relative+(anchor?'#'+encodeURIComponent(anchor):'');}
  return repo+'/tree/main/'+relative+(anchor?'#'+encodeURIComponent(anchor):'');
}
function render(markdown,source){
  const used=new Map();
  let html=marked.parse(markdown,{gfm:true,breaks:false});
  html=html.replace(/<h([1-6])>([\s\S]*?)<\/h\1>/g,(_,level,body)=>{
    const base=slug(body);const count=used.get(base)||0;used.set(base,count+1);
    return '<h'+level+' id="'+attribute(base+(count?'-'+count:''))+'">'+body+'</h'+level+'>';
  });
  html=html.replace(/\b(href|src)="([^"]*)"/g,(_,kind,href)=>kind+'="'+attribute(target(href,source))+'"');
  return html;
}
async function markdownFiles(relative){
  const result=[];
  for(const entry of await fs.readdir(path.join(root,relative),{withFileTypes:true})){
    const name=relative+'/'+entry.name;
    if(entry.isDirectory())result.push(...await markdownFiles(name));
    else if(entry.name.endsWith('.md'))result.push(name);
  }
  return result.sort();
}
const outputChapters=[];
for(const chapter of chapters){
  const markdown=await read(chapter.file);const html=render(markdown,chapter.file);
  const points=[...markdown.matchAll(/<a id="([^"]+)"><\/a>/g)];
  const searchSections=chapter.sections.map(section=>{
    const i=points.findIndex(p=>p[1]===section.id);const start=i<0?0:points[i].index;
    const end=i<0?markdown.length:(points[i+1]?.index??markdown.length);
    return {id:section.id,title:section.title,text:plain(marked.parse(markdown.slice(start,end)))};
  });
  outputChapters.push({...chapter,html,text:plain(html),searchSections});
}
const outputContests=[];
for(const contest of contests){
  const html=render(await read(contest.card_path),contest.card_path);
  outputContests.push({...contest,html,text:plain(html)});
}
const chapterSources=new Set(chapters.flatMap(c=>c.sections.map(s=>s.source).filter(Boolean)));
for(const relative of ['CONTRIBUTING.md','CHANGELOG.md',...await markdownFiles('docs'),...await markdownFiles('templates'),...await markdownFiles('examples')]){
  if(contestByFile.has(relative)||knownSupplements.has(relative))continue;
  knownSupplements.add(relative);const markdown=await read(relative);const html=render(markdown,relative);
  supplements.push({path:relative,title:plain(markdown.match(/^# (.+)$/m)?.[1]||relative),html,text:plain(html),searchable:!chapterSources.has(relative)&&!relative.includes('catalog-legacy')&&relative!=='docs/competition-catalog.md'});
}
const content={version:manifest.version,updated:'2026-11-17',siteURL,chapters:outputChapters,contests:outputContests,supplements};
const outputs=new Map();
for(const name of ['index.html','style.css','app.js','icon.svg'])outputs.set(name,await fs.readFile(path.join(root,'site',name)));
let index=outputs.get('index.html').toString('utf8');
// The first five ranks are present in the initial HTML too. Readers on a slow
// connection can see the ranking while the full searchable book is loading.
const preview=contests.filter(c=>Number.isInteger(c.rank)).sort((a,b)=>a.rank-b.rank).slice(0,5).map(c=>
  '<li class="home-rank-item" data-rank="'+c.rank+'"><a class="home-rank-link" href="#/home/top5-'+c.rank+'">'+
  '<span class="rank-number">'+c.rank+'</span><span class="rank-main"><strong class="rank-name">'+attribute(c.name)+'</strong><span class="rank-tool">'+attribute(c.homepage_tool_label||c.tool_name)+'</span></span><span class="rank-status">'+attribute(c.decision_label)+'</span></a></li>'
).join('\n');
if(!index.includes('<!-- HOME_RANK_PREVIEW -->'))throw Error('Missing initial ranking placeholder');
index=index.replace('<!-- HOME_RANK_PREVIEW -->',preview);
// Give each asset a content-derived URL so an already-open site receives the
// matching script and styles after publication rather than a stale cached pair.
for(const name of ['style.css','app.js']){
  const revision=createHash('sha256').update(outputs.get(name)).digest('hex').slice(0,12);
  index=index.replaceAll('./'+name+'"','./'+name+'?v='+revision+'"');
}
outputs.set('index.html',Buffer.from(index));
outputs.set('content.json',Buffer.from(JSON.stringify(content)));
outputs.set('.nojekyll',Buffer.from(''));
outputs.set('404.html',outputs.get('index.html'));
outputs.set('robots.txt',Buffer.from('User-agent: *\nAllow: /\nSitemap: '+siteURL+'sitemap.xml\n'));
outputs.set('sitemap.xml',Buffer.from('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+siteURL+'</loc></url></urlset>'));
for(const relative of [...copyFiles].sort()){
  if(!allowed(relative))throw Error('Refused non-public file '+relative);
  try{outputs.set(relative,await fs.readFile(path.join(root,relative)));}catch(error){throw Error('Linked file is missing: '+relative,{cause:error});}
}
for(const [name,bytes] of outputs)manifest.files[name]={bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')};
outputs.set('build-manifest.json',Buffer.from(JSON.stringify(manifest,null,2)+'\n'));
if(args.has('--check')){
  const stale=[];for(const [name,bytes] of outputs){try{if(!(await fs.readFile(path.join(output,name))).equals(bytes))stale.push(name);}catch{stale.push(name);}}
  if(stale.length)throw Error('Stale site files: '+stale.join(', '));
}else{
  // Write only known generated paths. Never delete a checkout or a user directory.
  await fs.mkdir(output,{recursive:true});
  for(const [name,bytes] of outputs){await fs.mkdir(path.dirname(path.join(output,name)),{recursive:true});await fs.writeFile(path.join(output,name),bytes);}
}
console.log(JSON.stringify({status:'passed',check:args.has('--check'),output:'_site',chapters:chapters.length,sections:chapters.reduce((n,c)=>n+c.sections.length,0),contests:contests.length,ranked:contests.filter(c=>c.rank).length,supplements:supplements.length,files:outputs.size,contentBytes:outputs.get('content.json').length}));
