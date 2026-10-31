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
function detailDialog(){
  let dialog=document.getElementById('record-detail-dialog');
  if(dialog)return dialog;
  dialog=el('dialog','record-dialog');
  dialog.id='record-detail-dialog';
  dialog.setAttribute('aria-labelledby','detail-title');
  const shell=el('div','dialog-shell');
  const header=el('div','dialog-header');
  const heading=el('div','');
  heading.append(el('p','eyebrow','RECORD REVIEW'));
  heading.append(el('h2','','Record details'));
  const close=el('button','dialog-close','×');
  close.type='button';close.setAttribute('aria-label','Close details');
  close.addEventListener('click',()=>dialog.close());
  header.append(heading,close);
  const body=el('div','dialog-body');body.id='record-detail-body';
  shell.append(header,body);dialog.append(shell);
  dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close();});
  document.body.append(dialog);
  return dialog;
}
function detailSection(host,title,value,ordered=false){
  if(value===undefined||value===null||value===''||(Array.isArray(value)&&!value.length))return;
  const section=el('section','detail-section');
  section.append(el('h3','',title));
  if(Array.isArray(value)){
    const list=el(ordered?'ol':'ul','detail-list');
    value.forEach(item=>{
      const li=el('li','',typeof item==='object'?JSON.stringify(item):item);
      list.append(li);
    });
    section.append(list);
  }else{
    section.append(el('p','detail-copy',value));
  }
  host.append(section);
}
function openRecordDetail(record,dataset){
  const dialog=detailDialog();
  const body=document.getElementById('record-detail-body');
  body.replaceChildren();
  const title=record.title||record.name||record.id||'Untitled record';
  body.append(el('h2','detail-title',title));
  const badges=el('div','record-meta');
  badges.append(makeTag(dataset==='source'?'Source record':dataset));
  badges.append(makeTag(statusOf(record,dataset),dataset==='quarantine'?'danger':dataset==='approved'?'':'warn'));
  if(record.category)badges.append(makeTag(record.category));
  if(record.content_type)badges.append(makeTag(record.content_type));
  body.append(badges);
  if(dataset==='quarantine'){
    detailSection(body,'Quarantine reason',record.quarantine_reason||'This record is quarantined and its instructional content is intentionally restricted.');
    detailSection(body,'Record ID',record.id);
    detailSection(body,'Stage classification',record.stage_ids);
    body.append(el('p','detail-warning','Instructional content is hidden because the source did not substantiate the operational detail. Re-source and review before restoring.'));
    dialog.showModal();
    return;
  }
  detailSection(body,'Summary',record.summary);
  detailSection(body,'Tutorial / procedure',record.steps,true);
  detailSection(body,'Materials',record.materials);
  detailSection(body,'Tools',record.tools);
  detailSection(body,'Prerequisites',record.prerequisites);
  detailSection(body,'Expected result',record.expected_result);
  detailSection(body,'Potential failure modes',record.failure_modes);
  detailSection(body,'Safety notes',record.safety_notes);
  detailSection(body,'Warnings and limitations',record.warnings);
  detailSection(body,'Identification criteria',record.identification_criteria);
  detailSection(body,'Edible parts',record.edible_parts);
  detailSection(body,'Preparation requirements',record.preparation_requirements);
  detailSection(body,'Lookalikes and uncertainty',record.lookalikes_or_uncertainty);
  detailSection(body,'Evidence excerpt',record.evidence_excerpt);
  detailSection(body,'Quality notes',record.quality_notes);
  if(record.verification){
    const v=record.verification;
    detailSection(body,'Verification',[
      'Status: '+(v.status||'Not specified'),
      'Confidence: '+(v.confidence||'Not specified'),
      'Reviewed by: '+(v.reviewed_by||'Not recorded'),
      'Reviewed at: '+(v.reviewed_at||'Not recorded')
    ]);
  }
  if(record.stage_classification){
    detailSection(body,'Stage classification',[
      'Suggested stages: '+(record.stage_classification.suggested_stage_ids||[]).join(', '),
      'Review status: '+(record.stage_classification.review_status||'Not specified'),
      'Method: '+(record.stage_classification.method||'Not specified'),
      'Reason: '+(record.stage_classification.reason||'Not specified')
    ]);
  }
  const sources=Array.isArray(record.sources)?record.sources:(record.url?[{title:record.title||record.name||record.url,url:record.url,domain:record.domain}]:[]);
  if(sources.length){
    const section=el('section','detail-section');section.append(el('h3','','Sources'));
    sources.forEach(source=>{
      const item=el('div','detail-source');
      const link=el('a','',source.title||source.url||'Open source');
      if(source.url){link.href=source.url;link.target='_blank';link.rel='noopener noreferrer';}
      item.append(link);
      if(source.domain)item.append(el('small','',source.domain));
      if(source.retrieved_at)item.append(el('small','', 'Retrieved: '+source.retrieved_at));
      section.append(item);
    });
    body.append(section);
  }
  if(dataset==='source'&&record.text)detailSection(body,'Extracted source text',record.text);
  detailSection(body,'Record ID',record.id);
  detailSection(body,'Last retrieved',record.retrieved_at);
  if(dataset!=='approved')body.append(el('p','detail-warning','Review status: this record is not automatically approved for practical use. Check the cited source, local applicability, and safety requirements before acting.'));
  else body.append(el('p','detail-note','Published record. Continue to follow local regulations and source guidance.'));
  dialog.showModal();
}
function renderExplorer(){
  const list=document.getElementById('record-list');if(!list)return;
  const term=document.getElementById('record-search').value.trim().toLowerCase();
  const dataset=document.getElementById('dataset-filter').value;
  const stage=document.getElementById('stage-filter').value;
  const filtered=explorerRecords.filter(({record:r,dataset:d})=>{
    if(dataset!=='all'&&dataset!==d)return false;
    if(stage&&!(r.stage_ids||r.stage_classification?.suggested_stage_ids||[]).includes(stage))return false;
    if(term&&![r.title,r.summary,r.id,r.category,r.url,r.name].some(v=>String(v||'').toLowerCase().includes(term)))return false;
    return true;
  });
  document.getElementById('result-count').textContent=filtered.length+' records shown';
  list.replaceChildren();
  if(!filtered.length){list.append(el('div','empty-state','No records match the selected filters.'));return;}
  const fragment=document.createDocumentFragment();
  filtered.slice(0,250).forEach(({record:r,dataset:d})=>{
    const card=el('article','record-card record-card-clickable');
    card.tabIndex=0;card.setAttribute('role','button');
    card.setAttribute('aria-label','Open details for '+(r.title||r.name||r.id||'record'));
    card.addEventListener('click',()=>openRecordDetail(r,d));
    card.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();openRecordDetail(r,d);}});
    const top=el('div','record-top');top.append(el('span','tag neutral',d==='source'?'Source record':d),makeTag(statusOf(r,d),d==='approved'?'':d==='quarantine'?'danger':'warn'));card.append(top);
    const title=d==='quarantine'?(r.title||r.id||'Quarantined record'):(r.title||r.name||r.url||r.id||'Untitled record');
    card.append(el('h3','',title));
    if(d!=='quarantine'&&r.summary)card.append(el('p','',r.summary.slice(0,360)));
    if(d==='quarantine')card.append(el('p','','Instructional content hidden pending re-sourcing and review.'));
    const meta=el('div','record-meta');
    if(r.category)meta.append(makeTag(r.category));
    if(r.content_type)meta.append(makeTag(r.content_type));
    if(r.stage_ids?.length)meta.append(makeTag(stageLabel(r.stage_ids)));
    if(r.id)meta.append(makeTag('ID: '+r.id,'neutral'));
    if(r.url){const link=el('a','tag','Open source ↗');link.href=r.url;link.target='_blank';link.rel='noopener noreferrer';link.addEventListener('click',event=>event.stopPropagation());meta.append(link);}
    meta.append(makeTag('Click to inspect','neutral'));
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
