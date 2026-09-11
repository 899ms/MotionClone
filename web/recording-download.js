// Download always means the selected branded recording view, including audio.
(() => {
  const button=$('download');
  const status=document.createElement('p');status.id='recording-export-status';status.setAttribute('role','status');status.hidden=true;
  $('finished').append(status);
  const raw=document.createElement('a');raw.id='download-rebuild-only';raw.className='secondary';raw.textContent='Rebuilt video only';raw.setAttribute('download','motionclone-rebuilt.mp4');
  $('export-details').append(raw);
  let pending=false;
  const savedShow=show;
  show=job=>{savedShow(job);if(job.files?.['output.mp4'])raw.href=job.files['output.mp4'];};
  function update(message,error=false){status.hidden=false;status.textContent=message;status.classList.toggle('export-error',error);}
  button.addEventListener('click',async event=>{
    event.preventDefault();if(pending||!current)return;
    const project=current.id,settings=window.recordingPresentation.settings();
    pending=true;button.setAttribute('aria-disabled','true');button.setAttribute('aria-busy','true');
    update(`Preparing ${settings.look} recording · ${settings.format} · with audio…`);
    try{
      let task=await api(`/api/jobs/${project}/recording`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(settings)});
      while(task.status==='queued'||task.status==='running'){
        update(`${task.stage} · ${task.progress}% · ${settings.look}, ${settings.format}`);
        await new Promise(resolve=>setTimeout(resolve,1000));
        task=await api(`/api/jobs/${project}/recording/${task.key}`);
      }
      if(task.status!=='complete')throw new Error(task.error||'Recording export failed. Click Download MP4 to retry.');
      const link=document.createElement('a');link.href=task.url;link.download=`motionclone-${settings.look}-${settings.format}.mp4`;document.body.append(link);link.click();link.remove();
      update('Recording MP4 ready — full video with audio. ');
      const again=document.createElement('a');again.href=task.url;again.download='';again.textContent='Download again';status.append(again);
    }catch(error){update(error.message,true);}
    finally{pending=false;button.removeAttribute('aria-disabled');button.removeAttribute('aria-busy');}
  });
})();
