// Library navigation wraps the existing import/editor workflow. Persisted jobs stay compatible.
let libraryJobs = [], libraryFilter = 'all', libraryLoaded = false, librarySignature = '', detailsId = '';
const originalBrief = brief;
brief = () => ({...originalBrief(), sampling:$('sampling').value});
const originalFillBrief = fillBrief;
fillBrief = value => {originalFillBrief(value); $('sampling').value=value.sampling||'standard';};

function editorPage() {
  $('library-view').hidden=true; $('editor-view').hidden=false;
  editorState();
  navigation(current?'open-library':'new-project');
  document.querySelectorAll('.card-preview video').forEach(video=>video.pause());
  renderScreen();window.scrollTo({top:0,behavior:'instant'});
}
function libraryPage() {
  $('editor-view').hidden=true; $('library-view').hidden=false;
  document.body.classList.remove('is-new');
  navigation('open-library');
  document.querySelectorAll('.card-preview video').forEach(video=>video.pause());
  $('result-video').pause(); $('source-video').pause();
  error(''); renderScreen();refreshLibrary(); window.scrollTo({top:0,behavior:'instant'});
}
function navigation(active) {
  $('page-location').textContent=active==='new-project'?'New video':current&&!$('editor-view').hidden?'Project':'Saved videos';
  for(const id of ['new-project','open-library']) {
    $(id).classList.toggle('active',id===active);
    if(id===active)$(id).setAttribute('aria-current','page');else $(id).removeAttribute('aria-current');
  }
}
function editorState() {
  const busy=!!current&&['queued','running'].includes(current.status);
  if(!$('editor-view').hidden)navigation(current?'open-library':'new-project');
  $('render-faithful').hidden=!current||!['faithful','hyperframes'].includes(current.brief.mode);
  document.body.classList.toggle('is-new',!current&&!$('editor-view').hidden);
  document.body.classList.toggle('is-building',busy);
  document.body.classList.toggle('is-project',!!current&&!busy);
  $('import-fields').disabled=busy||submitting;
  setControl('create',busy?'Rebuilding…':submitting?'Starting…':'Rebuild video',busy||submitting?'loader':'layers');
  $('create-form').setAttribute('aria-busy',String(busy||submitting));
  $('editor-description').textContent=!current?'Paste a video link or upload a file to get started.':busy?'Rebuilding your video. Your progress is saved.':current.brief.mode==='hyperframes'?'Watch your rebuild, compare it, then download.':current.brief.mode==='faithful'?'This export reuses the original video. Its text, artwork, and animation were not rebuilt.':'Preview, edit, and download your video.';
}
function fillDetails(job) {
  $('url').value=job.url||'';
  $('saved-name').value=job.name;
  $('saved-collection').value=job.collection||'';
  $('saved-tags').value=(job.tags||[]).join(', ');
  $('saved-notice').textContent='';
}
async function openProject(id) {
  if(submitting)return;
  try {
    const job=await api(`/api/jobs/${id}`);
    editing=false;lastPlan='';fillBrief(job.brief);fillDetails(job);show(job);
    localStorage.setItem('frameforge-project',job.id);editorPage();error('');
    window.history.replaceState({},'',`/?workspace=1&project=${job.id}`);
  } catch(e) {error(e.message);}
}
const originalShow = show;
show = job => {
  originalShow(job);
  editorState();
  if(detailsId!==job.id){view='result';switchView('result');fillDetails(job);detailsId=job.id;}
  $('library-details').hidden=false;
  $('render-faithful').hidden=!['faithful','hyperframes'].includes(job.brief.mode);
  $('render-faithful').disabled=['running','queued'].includes(job.status);
  if(job.status==='draft'&&['faithful','hyperframes'].includes(job.brief.mode))$('project-options').open=true;
  $('editor-title').textContent=job.name;
  $('editor-kind').textContent=job.brief.mode==='hyperframes'?'HYPERFRAMES · REBUILT LAYERS':job.brief.mode==='faithful'?'HYPERFRAMES · SOURCE FRAMES':job.status==='draft'?'SAVED VARIATION':job.brief.mode==='rebuild'?'REMOTION REBUILD':'ORIGINAL VIDEO';
  setControl('favorite',job.favorite?'Favorited':'Favorite','star');
  $('favorite').setAttribute('aria-pressed',String(!!job.favorite));
  setControl('archive',job.archived?'Restore to library':'Archive','archive');
  $('duplicate').disabled=(!job.plan&&!['faithful','hyperframes'].includes(job.brief.mode))||['running','queued'].includes(job.status);
  $('remotion-export').hidden=job.brief.mode!=='rebuild';
  $('hyperframes-export').hidden=!['faithful','hyperframes'].includes(job.brief.mode);
  $('verification-label').classList.toggle('needs-review',job.brief.mode==='hyperframes'&&!job.verification?.near_perfect);
  $('verification-label').textContent=job.brief.mode==='hyperframes'?(job.verification?.near_perfect?'REBUILT · MATCH CHECKED':'REBUILT · VISUAL DIFFERENCES REMAIN'):job.brief.mode==='faithful'?'ORIGINAL VIDEO · NOT RECONSTRUCTED':'EXPORT CHECKED';
  setControl('result-tab',job.brief.mode==='hyperframes'?'Rebuilt':job.brief.mode==='faithful'?'Original export':'Result','play');
  $('hyperframes-export').href=`/api/jobs/${job.id}/hyperframes`;
  $('remotion-export').href=`/api/jobs/${job.id}/remotion`;
  $('mode-label').textContent=job.brief.mode==='hyperframes'?'HYPERFRAMES · INDEPENDENT LAYERS':job.brief.mode==='faithful'?'HYPERFRAMES · ORIGINAL FRAMES':job.brief.mode==='rebuild'?'EDITABLE REMOTION LAYERS':'ORIGINAL VIDEO + BRANDING';
  if(job.scan)$('sheet-count').textContent=`${job.scan.decoded} SCANNED · ${job.scan.selected} SELECTED`;
  const index=libraryJobs.findIndex(item=>item.id===job.id);
  if(index>=0)libraryJobs[index]=job;
  renderScreen();
};

function node(tag, className, text) {
  const element=document.createElement(tag);
  if(className)element.className=className;
  if(text!==undefined)element.textContent=text;
  return element;
}
function duration(seconds) {
  const total=Math.max(0,Math.round(Number(seconds)||0));
  return `${Math.floor(total/60)}:${String(total%60).padStart(2,'0')}`;
}
const statusLabels={complete:'Ready',draft:'Draft',running:'Building',queued:'Queued',error:'Needs attention',cancelled:'Cancelled',interrupted:'Interrupted'};
function card(job) {
  const article=node('article','motion-card');
  const preview=node('div','card-preview');
  const url=job.files['output.mp4']||job.files['source.mp4'];
  if(url) {
    const thumbnail=node('button','card-thumbnail');
    thumbnail.type='button';thumbnail.setAttribute('aria-label',`Open ${job.name}`);
    const image=document.createElement('img');
    image.src=job.files['thumbnail.jpg']||`/media/${job.id}/thumbnail.jpg`;
    image.alt='';image.loading='lazy';
    image.addEventListener('error',()=>{image.remove();thumbnail.classList.add('thumbnail-missing');},{once:true});
    const play=node('span','thumbnail-open');play.append(icon('play'));
    thumbnail.append(image,play);thumbnail.addEventListener('click',()=>openProject(job.id));
    preview.append(thumbnail);
  } else {const placeholder=node('div','preview-placeholder',job.status==='error'?'Reference unavailable':job.status==='complete'||job.status==='draft'?'No preview yet':'Preparing reference…');placeholder.prepend(icon(job.status==='error'?'error':'video'));preview.append(placeholder);}
  const badge=node('span',`card-badge ${job.status}`,statusLabels[job.status]||job.status);badge.prepend(icon(job.status==='complete'?'check-circle':['error','interrupted'].includes(job.status)?'warning':['running','queued'].includes(job.status)?'loader':'file'));preview.append(badge);
  article.append(preview);
  if(['running','queued'].includes(job.status)) {
    const bar=node('div','card-progress'),fill=node('span');
    fill.style.width=`${Math.max(0,Math.min(100,job.progress||0))}%`;bar.append(fill);article.append(bar);
  }
  const body=node('div','card-body'),title=node('button','card-title',job.name);
  const sourceType=node('div','card-format',job.brief.mode==='hyperframes'?'EDITABLE REBUILD':job.brief.mode==='faithful'?'ORIGINAL EXPORT':'VIDEO PROJECT');
  sourceType.prepend(icon('layers'));body.append(sourceType);
  title.addEventListener('click',()=>openProject(job.id));body.append(title);
  const meta=node('div','card-meta');
  meta.append(node('span','',job.media?duration(job.media.duration):new Date(job.created*1000).toLocaleDateString()),
    node('span','','·'),node('span','collection-label',job.collection||'Unsorted'));
  body.append(meta);
  if(job.media){
    const specs=node('dl','card-specs');
    for(const [label,value] of [['Duration',duration(job.media.duration)],['Resolution',`${job.media.width} × ${job.media.height}`],['Frame rate',`${Math.round(job.media.fps*100)/100} fps`]]){
      const spec=node('div','');spec.append(node('dt','',label),node('dd','',value));specs.append(spec);
    }
    body.append(specs);
  }
  if(job.url){
    try{const source=new URL(job.url);if(['https:','http:'].includes(source.protocol)){
      const reference=node('a','card-reference');reference.href=source.href;reference.target='_blank';reference.rel='noopener noreferrer';
      const x=['x.com','www.x.com','twitter.com','www.twitter.com'].includes(source.hostname);
      reference.append(icon('link'),node('span','',x&&source.pathname.split('/')[1]?`@${source.pathname.split('/')[1]} · View reference`:'View original reference'),icon('external'));body.append(reference);
    }}catch{}
  }
  const bottom=node('div','card-bottom'),open=node('button','card-open');setControl(open,'Open project','arrow-right');
  open.addEventListener('click',()=>openProject(job.id));
  const favorite=node('button','card-favorite');favorite.append(icon('star'));
  favorite.setAttribute('aria-label',`${job.favorite?'Unfavorite':'Favorite'} ${job.name}`);
  favorite.setAttribute('aria-pressed',String(!!job.favorite));
  favorite.addEventListener('click',async()=>{
    favorite.disabled=true;
    try{await patchProject(job.id,{favorite:!job.favorite});}catch(e){error(e.message);}finally{favorite.disabled=false;}
  });
  const kind=node('span','card-source',job.brief.mode==='hyperframes'?'Editable HyperFrames':job.brief.mode==='faithful'?'Original video export':job.brief.mode==='rebuild'?'Legacy rebuild':'Original frames');
  bottom.append(open,kind,favorite);body.append(bottom);article.append(body);return article;
}

let recentSignature='';
function drawRecent() {
  const jobs=libraryJobs.filter(job=>!job.archived).sort((a,b)=>b.created-a.created).slice(0,6);
  const signature=JSON.stringify(jobs);
  if(signature!==recentSignature){
    $('recent-grid').replaceChildren(...jobs.map(card));
    recentSignature=signature;
  }
  $('recent-loading').hidden=libraryLoaded;
  $('recent-empty').hidden=!libraryLoaded||!!jobs.length;
}

function drawLibrary() {
  const query=$('library-search').value.trim().toLowerCase(),collection=$('collection-filter').value;
  let jobs=libraryJobs.filter(job=>{
    if(!!job.archived!==(libraryFilter==='archived'))return false;
    if(libraryFilter==='favorites'&&!job.favorite)return false;
    if(libraryFilter==='ready'&&job.status!=='complete')return false;
    if(libraryFilter==='working'&&!['running','queued'].includes(job.status))return false;
    if(collection&&job.collection!==collection)return false;
    return !query||[job.name,job.collection,...(job.tags||[])].join(' ').toLowerCase().includes(query);
  });
  jobs.sort($('library-sort').value==='name'?(a,b)=>a.name.localeCompare(b.name):(a,b)=>b.created-a.created);
  const signature=JSON.stringify(jobs.map(j=>[j.id,j.name,j.status,j.favorite,j.collection,j.tags,j.progress,j.updated,j.files]));
  if(signature!==librarySignature){
    const grid=$('library-grid'),existing=new Map([...grid.children].map(element=>[element.dataset.id,element]));
    const ids=new Set(jobs.map(job=>job.id));
    for(const [id,element] of existing)if(!ids.has(id))element.remove();
    jobs.forEach((job,index)=>{
      const version=JSON.stringify([job.name,job.status,job.favorite,job.collection,job.tags,job.progress,job.updated,job.files]);
      let element=existing.get(job.id);
      if(!element||element.dataset.version!==version){
        const replacement=card(job);replacement.dataset.id=job.id;replacement.dataset.version=version;
        if(element)element.replaceWith(replacement);element=replacement;
      }
      if(grid.children[index]!==element)grid.insertBefore(element,grid.children[index]||null);
    });
    librarySignature=signature;
  }
  $('library-empty').hidden=!!jobs.length||!libraryLoaded;
  $('library-count').textContent=libraryLoaded?`${jobs.length} ${jobs.length===1?'video':'videos'}`:'Loading…';
  const filtered=!!(query||collection||libraryFilter!=='all');
  $('empty-title').textContent=filtered?'No matching videos':'No saved videos yet';
  $('empty-copy').textContent=filtered?'Try another search or filter.':'Import your first video. It will be saved here automatically.';
  $('empty-add').hidden=filtered;$('library-empty-art').src='/static/assets/illustration-'+(filtered?'search':'empty')+'.svg';
}
refreshLibrary = async () => {
  try {
    libraryJobs=await api('/api/library');libraryLoaded=true;
    const selected=$('collection-filter').value;
    const collections=[...new Set(libraryJobs.map(j=>j.collection).filter(Boolean))].sort();
    $('collection-filter').replaceChildren(new Option('All collections',''),...collections.map(c=>new Option(c,c)));
    $('collection-filter').value=collections.includes(selected)?selected:'';
    drawLibrary();drawRecent();$('library-load-error').hidden=true;renderScreen();return libraryJobs;
  } catch(e) {$('recent-loading').hidden=true;$('library-load-error').hidden=false;return [];}
};
async function patchProject(id,patch) {
  const job=await api(`/api/jobs/${id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(patch)});
  if(current?.id===id)show(job);
  await refreshLibrary();return job;
}

$('back-library').addEventListener('click',libraryPage);
$('open-library').addEventListener('click',libraryPage);
$('view-all').addEventListener('click',libraryPage);
for(const id of ['add-reference','empty-add'])$(id).addEventListener('click',()=>{$('new-project').click();});
$('new-project').addEventListener('click',()=>{
  if(submitting)return;
  if(current&&['running','queued'].includes(current.status))return;
  $('library-details').hidden=true;$('library-details').open=false;
  $('project-options').open=false;
  window.history.replaceState({},'','/?workspace=1');
  $('editor-title').textContent='Rebuild a video.';$('editor-kind').textContent='NEW REFERENCE';editorPage();
});
$('library-search').addEventListener('input',drawLibrary);
for(const id of ['collection-filter','library-sort'])$(id).addEventListener('change',drawLibrary);
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{
  libraryFilter=button.dataset.filter;
  document.querySelectorAll('[data-filter]').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',String(b===button));});drawLibrary();
}));
$('save-details').addEventListener('click',async()=>{
  if(!current)return;
  try{const job=await patchProject(current.id,{name:$('saved-name').value,collection:$('saved-collection').value,
    tags:$('saved-tags').value.split(',').map(t=>t.trim()).filter(Boolean)});fillDetails(job);$('saved-notice').textContent='Details saved.';error('');}
  catch(e){error(e.message);}
});
$('favorite').addEventListener('click',async()=>{if(current)try{await patchProject(current.id,{favorite:!current.favorite});}catch(e){error(e.message);}});
$('archive').addEventListener('click',async()=>{if(current)try{await patchProject(current.id,{archived:!current.archived});libraryPage();}catch(e){error(e.message);}});
$('duplicate').addEventListener('click',async()=>{
  if(!current)return;$('duplicate').disabled=true;
  try{const job=await api(`/api/jobs/${current.id}/duplicate`,{method:'POST'});await refreshLibrary();await openProject(job.id);
    $('saved-notice').textContent=current.brief.mode==='hyperframes'?'Rebuilt layers copied. Open Options to render this version.':current.brief.mode==='faithful'?'Original video copied. Open Options to export it.':'Copy saved. Change the text below, then Render edits. No new analysis needed.';}
  catch(e){error(e.message);}finally{$('duplicate').disabled=false;}
});
// Keep saved videos current while the library is visible.
setInterval(()=>{if(!$('library-view').hidden||document.body.classList.contains('is-new'))refreshLibrary();},6000);

// One state pass for the shared import, progress, result, and navigation surfaces.
function renderScreen(){
  const job=current,busy=!!job&&['queued','running'].includes(job.status),complete=job?.status==='complete';
  const active=busy?job:libraryJobs.find(item=>['queued','running'].includes(item.status));
  $('active-project').hidden=!active||busy&&!$('editor-view').hidden;
  $('active-project').dataset.job=active?.id||'';
  $('source-summary').hidden=!busy;
  $('source-summary-text').textContent=job?.url||job?.name||'Uploaded video';
  $('export-details').hidden=!complete;
  $('viewer-tabs').hidden=!job?.files?.['output.mp4']&&!job?.files?.['preview.mp4'];
  $('cancel').disabled=busy&&(cancellingId===job.id||job.stage?.startsWith('Cancelling'));
  if(!busy)cancellingId='';
  setControl('cancel',$('cancel').disabled?'Cancelling…':'Cancel',$('cancel').disabled?'loader':'stop');
  if(job){
    $('job-error-title').textContent=job.status==='cancelled'?'Rebuild cancelled':job.status==='interrupted'?'Rebuild interrupted':'Couldn’t finish this video';
    $('editor-description').textContent=['error','cancelled','interrupted'].includes(job.status)?'Your project is saved. Retry or choose another video.':$('editor-description').textContent;
    const stageIcon=job.progress>=95?'compare':job.progress>=60?'render':job.progress>=15?'layers':'download';
    setControl('job-state',busy?'IN PROGRESS':'',stageIcon);
    if(complete){
      const rebuilt=job.brief.mode==='hyperframes',matched=!!job.verification?.near_perfect;
      $('finished-title').textContent=rebuilt?(matched?'Your rebuilt video is ready.':'Your video is ready.'):job.brief.mode==='faithful'?'Original video export.':'Your export is ready.';
      $('finished-summary').textContent=rebuilt?(matched?'Compare the result, then download your video or editable project.':'Visual differences remain. Compare before using the result.'):job.brief.mode==='faithful'?'This export retains the original video; its visuals were not reconstructed.':'Download your video or open its project.';
      if(!$('verification-label').querySelector('svg'))$('verification-label').prepend(icon(rebuilt&&!matched?'warning':'check-circle'));
    }
  }
  decorateControls();
}
$('active-project').addEventListener('click',()=>{const id=$('active-project').dataset.job;if(id)openProject(id);});
$('choose-video').addEventListener('click',()=>{$('new-project').click();$('url').focus();});
$('library-retry').addEventListener('click',refreshLibrary);
