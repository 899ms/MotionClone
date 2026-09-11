const assetBase = new URL('.', document.currentScript.src);
// Local visitors already installed the app: take them directly to their workspace.
if (assetBase.pathname === '/static/' && ['127.0.0.1', 'localhost'].includes(location.hostname) && !new URLSearchParams(location.search).has('demo')) {
  location.replace('/?workspace=1');
}
function icon(name) {
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('class','icon');svg.setAttribute('aria-hidden','true');
  const use=document.createElementNS(svg.namespaceURI,'use');use.setAttribute('href',new URL('assets/icons.svg#'+name,assetBase));svg.append(use);return svg;
}
function setControl(element,text,name){element.replaceChildren(icon(name),document.createTextNode(text));}
function duration(seconds){const total=Math.max(0,Math.round(Number(seconds)||0));return `${Math.floor(total/60)}:${String(total%60).padStart(2,'0')}`;}
document.addEventListener('DOMContentLoaded',async()=>{
  document.querySelectorAll('[data-icon]').forEach(element=>element.prepend(icon(element.dataset.icon)));
  setupShowcaseInteractions();
  const local=['127.0.0.1','localhost'].includes(location.hostname);
  if(!local){const link=document.getElementById('open-workspace');link.href='#get-started';link.firstChild.textContent='Get started ';}
  if(local){
    try{
      const response=await fetch('/api/library',{signal:AbortSignal.timeout(4000)});
      if(!response.ok)throw new Error('No local workspace');
      const jobs=await response.json();
      const job=jobs.find(job=>!job.archived&&job.status==='complete'&&job.brief.mode==='hyperframes'&&job.files['source.mp4']&&job.files['output.mp4']);
      if(job){
        if(job.media?.width&&job.media?.height)document.getElementById('demo').style.setProperty('--media-ratio',job.media.width/job.media.height);
        document.getElementById('demo-player').replaceChildren(comparisonPreview(job));
        document.getElementById('speed-control').hidden=false;
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

function setupShowcaseInteractions(){
  const demo=document.getElementById('demo');
  const pair=document.getElementById('view-pair'),wipe=document.getElementById('view-wipe');
  function setView(wiping){
    demo.classList.toggle('wipe-mode',wiping);
    pair.setAttribute('aria-pressed',String(!wiping));wipe.setAttribute('aria-pressed',String(wiping));
    document.getElementById('wipe-control').hidden=!wiping;
  }
  pair.addEventListener('click',()=>setView(false));wipe.addEventListener('click',()=>setView(true));
  document.getElementById('wipe-position').addEventListener('input',event=>{demo.style.setProperty('--wipe',event.target.value+'%');demo.style.setProperty('--wipe-number',Number(event.target.value)/100);});
  document.getElementById('demo-speed').addEventListener('change',event=>demo.querySelectorAll('video').forEach(video=>{video.playbackRate=Number(event.target.value);}));
  const expand=document.getElementById('demo-expand');
  if(!demo.requestFullscreen)expand.hidden=true;
  expand.addEventListener('click',async()=>{
    try{if(document.fullscreenElement)await document.exitFullscreen();else await demo.requestFullscreen();}
    catch{document.getElementById('demo-footnote').textContent='Fullscreen is unavailable in this browser. The inline demo still works.';}
  });
  document.addEventListener('fullscreenchange',()=>expand.setAttribute('aria-label',document.fullscreenElement?'Exit fullscreen':'View demo fullscreen'));
  const scene=document.querySelector('.layer-scene');
  document.querySelectorAll('[data-layer]').forEach(button=>button.addEventListener('click',()=>{
    const visible=button.getAttribute('aria-pressed')!=='true';button.setAttribute('aria-pressed',String(visible));
    scene.querySelector('[data-plane="'+button.dataset.layer+'"]').classList.toggle('plane-hidden',!visible);
    const count=document.querySelectorAll('[data-layer][aria-pressed="true"]').length;
    document.getElementById('layer-count').textContent=count+' '+(count===1?'layer':'layers')+' visible';
  }));
  const explode=document.getElementById('explode-layers');
  explode.addEventListener('click',()=>{
    const separated=scene.classList.toggle('exploded');explode.setAttribute('aria-pressed',String(separated));
    setControl(explode,separated?'Put the layers together':'Separate the layers','layers');
  });
  // Pointer response is confined to the decorative hero tiles, without layout shifts.
  const hero=document.querySelector('.hero');let pending=0,lastEvent=null;
  hero.addEventListener('pointermove',event=>{
    if(matchMedia('(prefers-reduced-motion: reduce)').matches||event.pointerType!=='mouse')return;
    lastEvent=event;if(pending)return;
    pending=requestAnimationFrame(()=>{pending=0;const box=hero.getBoundingClientRect();hero.style.setProperty('--pointer-x',((lastEvent.clientX-box.left)/box.width-.5)*14+'px');hero.style.setProperty('--pointer-y',((lastEvent.clientY-box.top)/box.height-.5)*10+'px');});
  });
  hero.addEventListener('pointerleave',()=>{cancelAnimationFrame(pending);pending=0;hero.style.setProperty('--pointer-x','0px');hero.style.setProperty('--pointer-y','0px');});
}
