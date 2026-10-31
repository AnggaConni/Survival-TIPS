const DATA_BASE = 'data/';
const DATA_FILES = {
  approved: 'approved_tips.json',
  active: 'tips.json',
  candidates: 'candidate_tips.json',
  quarantine: 'tips.quarantine.json',
  sources: 'sources.json',
  activeReport: 'quality_report_active.json',
  candidateReport: 'quality_report_candidates.json',
  approvedReport: 'quality_report_approved.json',
  species: 'species.json',
  recipes: 'recipes.json',
  materials: 'materials.json',
  biodiversity: 'biodiversity_profiles.json',
  agriculture: 'agriculture_profiles.json'
};
const STAGES = ['01-drr','02-biodiversity','03-water-sanitation','04-agriculture','05-energy','06-materials','07-manufacturing','08-infrastructure'];
const cache = {};
async function loadJson(file) {
  if (cache[file]) return cache[file];
  const response = await fetch(DATA_BASE + file, {cache:'no-store'});
  if (!response.ok) throw new Error('HTTP ' + response.status);
  const value = await response.json();
  cache[file] = value;
  return value;
}
function records(value) { return Array.isArray(value) ? value : (value && Array.isArray(value.tips) ? value.tips : (value && Array.isArray(value.sources) ? value.sources : [])); }
function el(tag, className, text) { const node=document.createElement(tag); if(className) node.className=className; if(text!==undefined) node.textContent=String(text); return node; }
function stat(name,value){document.querySelectorAll('[data-stat="'+name+'"]').forEach(n=>n.textContent=value);}
function statusOf(record, dataset) {
  if(dataset==='approved') return 'Approved publication';
  if(dataset==='candidates') return 'AI candidate · review required';
  if(dataset==='quarantine') return 'Quarantined · restricted preview';
  const s=record.verification?.status || record.review_status || record.quality_status || 'Needs review';
  return String(s).replaceAll('_',' ');
}
function stageLabel(ids){return Array.isArray(ids)&&ids.length?ids.join(', '):'Stage not classified';}
function makeTag(text,kind=''){return el('span','tag '+kind,text);}
async function initDashboard(){
  try {
    const [a,p,c,s]=await Promise.all([loadJson(DATA_FILES.approved),loadJson(DATA_FILES.active),loadJson(DATA_FILES.candidates),loadJson(DATA_FILES.sources)]);
    stat('approved',records(a).length);stat('pending',records(p).length);stat('sources',records(s).length);
  } catch(e){console.warn('Dashboard summary unavailable',e);document.querySelectorAll('#overview-stats .stat-card b').forEach(n=>n.textContent='—');}
}
let explorerRecords=[];
async function initExplorer(){
  const list=document.getElementById('record-list'); if(!list)return;
  const params=new URLSearchParams(location.search); const initialStage=params.get('stage')||'';
  const stageFilter=document.getElementById('stage-filter'); if(initialStage && STAGES.includes(initialStage))stageFilter.value=initialStage;
  const jobs=await Promise.allSettled([
    loadJson(DATA_FILES.approved),loadJson(DATA_FILES.active),loadJson(DATA_FILES.candidates),loadJson(DATA_FILES.quarantine),loadJson(DATA_FILES.sources)
  ]);
  const [a,p,c,q,s]=jobs.map(x=>x.status==='fulfilled'?x.value:null);
  stat('approved',a?records(a).length:'!');stat('active',p?records(p).length:'!');stat('candidates',c?records(c).length:'!');stat('sources',s?records(s).length:'!');
  const datasets=[['approved',a],['active',p],['candidates',c],['quarantine',q]];
  explorerRecords=[];
  for(const [dataset,payload] of datasets){
    if(!payload)continue;
    for(const r of records(payload)) explorerRecords.push({record:r,dataset});
  }
  if(s) for(const r of records(s)) explorerRecords.push({record:r,dataset:'source'});
  renderExplorer();
  document.getElementById('record-search').addEventListener('input',renderExplorer);
  document.getElementById('dataset-filter').addEventListener('change',renderExplorer);
  stageFilter.addEventListener('change',renderExplorer);
}
function renderExplorer(){
  const list=document.getElementById('record-list'); if(!list)return;
  const term=document.getElementById('record-search').value.trim().toLowerCase();
  const dataset=document.getElementById('dataset-filter').value;
  const stage=document.getElementById('stage-filter').value;
  const filtered=explorerRecords.filter(({record:r,dataset:d})=>{
    if(dataset!=='all' && dataset!==d)return false;
    if(stage && !(r.stage_ids||[]).includes(stage))return false;
    if(term && ![r.title,r.summary,r.id,r.category,r.url,r.name].some(v=>String(v||'').toLowerCase().includes(term)))return false;
    return true;
  });
  document.getElementById('result-count').textContent=filtered.length+' records shown';
  list.replaceChildren();
  if(!filtered.length){list.append(el('div','empty-state','No records match the selected filters.'));return;}
  const fragment=document.createDocumentFragment();
  filtered.slice(0,250).forEach(({record:r,dataset:d})=>{
    const card=el('article','record-card');
    const top=el('div','record-top');top.append(el('span','tag neutral',d==='source'?'Source record':d),makeTag(statusOf(r,d),d==='approved'?'':d==='quarantine'?'danger':'warn'));card.append(top);
    // Quarantined entries intentionally expose metadata only, never instructions or full summaries.
    const title=d==='quarantine'?(r.title||r.id||'Quarantined record'):(r.title||r.name||r.url||r.id||'Untitled record');
    card.append(el('h3','',title));
    if(d!=='quarantine' && r.summary)card.append(el('p','',r.summary.slice(0,360)));
    if(d==='quarantine')card.append(el('p','','Content preview hidden. Inspect the record in the repository with appropriate review access.'));
    const meta=el('div','record-meta');
    if(r.category)meta.append(makeTag(r.category));
    if(r.content_type)meta.append(makeTag(r.content_type));
    if(r.stage_ids?.length)meta.append(makeTag(stageLabel(r.stage_ids)));
    if(r.id)meta.append(makeTag('ID: '+r.id,'neutral'));
    if(r.url){const link=el('a','tag', 'Open source ↗');link.href=r.url;link.target='_blank';link.rel='noopener noreferrer';meta.append(link);}
    card.append(meta);fragment.append(card);
  });
  list.append(fragment);
  if(filtered.length>250)list.append(el('p','muted','Showing first 250 results. Narrow your search to see more.'));
}
async function initQuality(){
  const host=document.getElementById('quality-issues');if(!host)return;
  const reportJobs=await Promise.allSettled([loadJson(DATA_FILES.activeReport),loadJson(DATA_FILES.candidateReport),loadJson(DATA_FILES.approvedReport)]);
  const reports=reportJobs.map(x=>x.status==='fulfilled'?x.value:null).filter(Boolean);
  const active=reports.find(r=>r.dataset==='tips.json')||reports[0]||{};
  document.getElementById('flagged-count').textContent=active.flagged_tip_count??'—';
  document.getElementById('duplicate-count').textContent=active.possible_duplicate_pairs?.length??'—';
  document.getElementById('conflict-count').textContent=active.possible_conflict_pairs?.length??'—';
  document.getElementById('report-date').textContent=active.generated_at?'Audit: '+new Date(active.generated_at).toLocaleString():'No report found';
  host.replaceChildren();
  const flagged=active.flagged_issues||{};
  const ids=Object.keys(flagged);
  if(!ids.length)host.append(el('div','empty-state','No flagged issues in the available active audit report, or no report could be loaded.'));
  ids.forEach(id=>{
    const card=el('article','issue-card');card.append(el('h3','',id));
    const reasons=flagged[id]||[];reasons.forEach(reason=>card.append(el('p','',reason.replaceAll('_',' '))));
    host.append(card);
  });
  const duplicatePairs=active.possible_duplicate_pairs||[];
  const conflictPairs=active.possible_conflict_pairs||[];
  [...duplicatePairs.map(p=>({kind:'Possible duplicate',p})),...conflictPairs.map(p=>({kind:'Possible conflict',p}))].forEach(({kind,p})=>{
    const card=el('article','issue-card');card.append(el('h3','',kind+': '+p.left_id+' ↔ '+p.right_id));
    card.append(el('p','',p.status||'Triage signal only — human review required.'));
    if(p.signals?.length)card.append(el('p','',p.signals.join(', ').replaceAll('_',' ')));
    host.append(card);
  });
  await runIntegrityChecks();
}
async function runIntegrityChecks(){
  const host=document.getElementById('integrity-results');if(!host)return;
  const files=['sources.json','tips.json','candidate_tips.json','approved_tips.json','tips.quarantine.json','species.json','recipes.json','materials.json','biodiversity_profiles.json','agriculture_profiles.json','quality_report_active.json'];
  let passed=0,failed=0;host.replaceChildren();
  for(const file of files){
    const row=el('div','integrity-item');row.append(el('b','',file));
    try{
      const data=await loadJson(file);const isArray=Array.isArray(data)||data&&typeof data==='object';
      if(!isArray)throw new Error('Unexpected root type');
      const collection=records(data);
      const ids=collection.map(x=>x.id).filter(Boolean);
      const duplicateIds=ids.filter((id,i)=>ids.indexOf(id)!==i);
      if(duplicateIds.length)throw new Error('Duplicate IDs: '+[...new Set(duplicateIds)].join(', '));
      row.append(el('span','integrity-ok','✓ Parsed · '+collection.length+' records'));passed++;
    }catch(e){row.append(el('span','integrity-fail','✕ '+e.message));failed++;}
    host.append(row);
  }
  const count=document.getElementById('json-count');if(count)count.textContent=passed+'/'+files.length;
  const summary=el("p","muted",failed?failed+" browser-level check(s) failed. This is a lightweight check, not the repository full validator.":"All "+passed+" selected files passed lightweight browser checks.");
  host.append(summary);
}
document.addEventListener('DOMContentLoaded',()=>{
  if(document.getElementById('overview-stats'))initDashboard();
  if(document.getElementById('record-list'))initExplorer().catch(e=>{document.getElementById('record-list').textContent='Unable to load datasets: '+e.message;});
  if(document.getElementById('quality-issues'))initQuality().catch(e=>console.error('Quality monitor error',e));
});
