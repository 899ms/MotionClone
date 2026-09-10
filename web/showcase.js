const assetBase = new URL('.', document.currentScript.src);
function icon(name) {
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('class','icon');svg.setAttribute('aria-hidden','true');
  const use=document.createElementNS(svg.namespaceURI,'use');use.setAttribute('href',new URL('assets/icons.svg#'+name,assetBase));svg.append(use);return svg;
}
function setControl(element,text,name){element.replaceChildren(icon(name),document.createTextNode(text));}
function duration(seconds){const total=Math.max(0,Math.round(Number(seconds)||0));return `${Math.floor(total/60)}:${String(total%60).padStart(2,'0')}`;}
document.addEventListener('DOMContentLoaded',async()=>{
  document.querySelectorAll('[data-icon]').forEach(element=>element.prepend(icon(element.dataset.icon)));
  const local=['127.0.0.1','localhost'].includes(location.hostname);
  if(!local){const link=document.getElementById('open-workspace');link.href='#get-started';link.firstChild.textContent='Get started ';}
  if(local){
    try{
      const response=await fetch('/api/library',{signal:AbortSignal.timeout(4000)});
      if(!response.ok)throw new Error('No local workspace');
      const jobs=await response.json();
      const job=jobs.find(job=>!job.archived&&job.status==='complete'&&job.brief.mode==='hyperframes'&&job.files['source.mp4']&&job.files['output.mp4']);
      if(job){
        document.getElementById('demo-player').replaceChildren(comparisonPreview(job));
        document.getElementById('demo-tag').textContent='ACTUAL REBUILD';
        document.getElementById('demo-description').replaceChildren(icon('layers'),document.createTextNode(job.name));
        document.getElementById('demo-footnote').textContent='Real reference. Independent rebuild. Visual differences are shown as they are.';
      }
    }catch{/* The standalone illustration remains available without a local server. */}
  }
  document.getElementById('copy-command').addEventListener('click',async()=>{
    const text=document.getElementById('install-command').textContent;
    try{await navigator.clipboard.writeText(text);document.getElementById('copy-notice').textContent='Copied. Paste into PowerShell.';}
    catch{const range=document.createRange();range.selectNodeContents(document.getElementById('install-command'));const selection=getSelection();selection.removeAllRanges();selection.addRange(range);document.getElementById('copy-notice').textContent='Command selected. Press Ctrl+C to copy.';}
  });
  const watch=document.querySelector('.demo-button');watch.addEventListener('click',()=>{
    const player=[...comparisons].find(player=>document.getElementById('demo-player').contains(player.root));
    if(player){player.manual=true;player.update();}
  });
});
