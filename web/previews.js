// Shared lifecycle: only visible comparisons decode video; removed cards release resources.
const comparisons = new Set();
const previewMotion = matchMedia('(prefers-reduced-motion: reduce)');
const previewObserver = new IntersectionObserver(entries => {
  for (const entry of entries) {
    const player = [...comparisons].find(item => item.root === entry.target);
    if (player) player.visible = entry.isIntersecting;
  }
  comparisons.forEach(player => player.update());
}, {threshold: .15});

function comparisonPreview(job) {
  const root = document.createElement('div'); root.className = 'live-comparison';
  const videos = [];
  const resultLabel = ['hyperframes','rebuild'].includes(job.brief.mode) ? 'Rebuilt' : 'Export';
  for (const [label, file, type] of [['Original', 'source.mp4', 'original'], [resultLabel, 'output.mp4', 'rebuilt']]) {
    const pane = document.createElement('figure'); pane.className = 'compare-pane ' + type;
    const caption = document.createElement('figcaption');
    caption.append(icon(type === 'original' ? 'video' : 'layers'), document.createTextNode(label));
    const video = document.createElement('video');
    video.src = job.files[file]; video.muted = true; video.playsInline = true;
    video.preload = 'metadata'; video.setAttribute('aria-label', `${label}: ${job.name}`);
    // Do not use the original thumbnail as a poster for the rebuilt result.
    pane.append(caption, video); root.append(pane); videos.push(video);
  }
  const bar = document.createElement('div'); bar.className = 'compare-controls';
  const toggle = document.createElement('button'); toggle.className = 'compare-toggle';
  const seek = document.createElement('input'); seek.type = 'range'; seek.min = 0;
  seek.max = job.media?.duration || 1; seek.step = .01; seek.value = 0;
  seek.setAttribute('aria-label', `Seek both videos: ${job.name}`);
  const time = document.createElement('span'); time.className = 'compare-time';
  const sound = document.createElement('button'); sound.className = 'compare-sound';
  sound.append(icon('audio')); sound.setAttribute('aria-label', 'Unmute original audio');
  sound.setAttribute('aria-pressed', 'false'); sound.title = 'Original audio only';
  const state = document.createElement('span'); state.className = 'compare-state';
  bar.append(toggle, seek, time, sound); root.append(bar, state);
  const player = {
    root, videos, visible: false, manual: null, playing: false, pending: false, failed: false,
    allowed() {return this.visible && !document.hidden && !this.failed && (this.manual ?? !previewMotion.matches) && (this.manual === true || [...comparisons].filter(p => p.visible).slice(0,2).includes(this));},
    pause() {videos.forEach(v => v.pause()); this.playing = false; this.paint();},
    paint() {
      setControl(toggle, this.playing ? 'Pause' : 'Play', this.playing ? 'pause' : 'play');
      toggle.setAttribute('aria-label', this.playing ? 'Pause both videos' : 'Play both videos');
      time.textContent = `${duration(videos[0].currentTime)} / ${duration(Number(seek.max))}`;
      state.textContent = this.failed ? 'Preview unavailable. Open the project to retry.' : this.playing ? `Playing in sync · ${videos[0].muted ? 'Muted' : 'Original audio'}` : `Original on the left · ${resultLabel.toLowerCase()} on the right`;
    },
    async update() {
      if (!this.allowed()) {this.pause(); return;}
      if (this.playing || this.pending) return;
      if (videos.some(v => v.readyState < 3)) {videos.forEach(v => {if(v.preload !== 'auto'){v.preload='auto';v.load();}});state.textContent = 'Loading both previews…'; return;}
      this.pending = true;
      if (Math.abs(videos[1].currentTime - videos[0].currentTime) > .08) videos[1].currentTime = videos[0].currentTime;
      try {
        await Promise.all(videos.map(v => v.play()));
        if (this.allowed()) this.playing = true; else this.pause();
      } catch {this.manual = false; this.pause();}
      finally {this.pending = false; this.paint();}
    },
    destroy() {this.manual = false; this.pause(); previewObserver.unobserve(root); videos.forEach(v => {v.removeAttribute('src'); v.load();}); comparisons.delete(this);}
  };
  toggle.addEventListener('click', () => {player.manual = !player.playing; player.update();});
  seek.addEventListener('input', () => {videos.forEach(v => {v.currentTime = Number(seek.value);}); player.paint();});
  sound.addEventListener('click', () => {
    videos[0].muted = !videos[0].muted;
    sound.setAttribute('aria-pressed', String(!videos[0].muted));
    sound.setAttribute('aria-label', videos[0].muted ? 'Unmute original audio' : 'Mute original audio');
    player.paint();
  });
  videos.forEach(video => {
    video.addEventListener('canplay', () => player.update());
    video.addEventListener('waiting', () => {player.pause(); state.textContent = 'Buffering both previews…';});
    video.addEventListener('ended', () => {player.pause(); videos.forEach(v => {v.currentTime = 0;}); player.update();});
    video.addEventListener('error', () => {player.failed = true; player.pause();});
    video.addEventListener('loadedmetadata', () => {
      const durations=videos.map(v=>v.duration).filter(d=>Number.isFinite(d)&&d>0);
      if(durations.length)seek.max=Math.min(...durations);
      player.paint();
    });
  });
  player.paint(); comparisons.add(player); previewObserver.observe(root);
  return root;
}
let previewTick = 0;
function updateComparisons(now) {
  if (now - previewTick > 120) {
    previewTick = now;
    for (const player of comparisons) {
      if (!player.root.isConnected) {player.destroy(); continue;}
      if (!player.playing) continue;
      const [original, rebuilt] = player.videos;
      if (Math.abs(original.currentTime - rebuilt.currentTime) > .12 && !rebuilt.seeking) rebuilt.currentTime = original.currentTime;
      const seek = player.root.querySelector('input');
      seek.value = original.currentTime;
      player.root.querySelector('.compare-time').textContent = `${duration(original.currentTime)} / ${duration(Number(seek.max))}`;
    }
  }
  requestAnimationFrame(updateComparisons);
}
requestAnimationFrame(updateComparisons);
document.addEventListener('visibilitychange', () => comparisons.forEach(player => player.update()));
previewMotion.addEventListener('change', () => comparisons.forEach(player => player.update()));

// Original GLSL light field, clipped behind the comparison; no third-party runtime.
function mountStudioLight() {
  const host = document.getElementById('recent-section');
  const canvas = document.createElement('canvas'); canvas.className = 'studio-light'; canvas.setAttribute('aria-hidden', 'true');
  host.prepend(canvas);
  const gl = canvas.getContext('webgl', {alpha:true, antialias:false, depth:false, premultipliedAlpha:false});
  if (!gl) {canvas.remove(); return;}
  const shader = (type, source) => {const s = gl.createShader(type); gl.shaderSource(s,source); gl.compileShader(s); if (!gl.getShaderParameter(s,gl.COMPILE_STATUS)) throw new Error('Shader unavailable'); return s;};
  try {
    const vertex = shader(gl.VERTEX_SHADER, 'attribute vec2 p; void main(){gl_Position=vec4(p,0.,1.);}');
    const fragment = shader(gl.FRAGMENT_SHADER, `precision mediump float; uniform vec2 size; uniform float t;
      void main(){vec2 uv=gl_FragCoord.xy/size; vec2 p=uv-vec2(.68+.10*sin(t*.16),.55+.12*cos(t*.13));
      float bloom=exp(-dot(p*vec2(1.1,1.8),p*vec2(1.1,1.8))*8.);
      float ribbon=pow(.5+.5*sin(uv.x*7.+uv.y*4.+sin(uv.y*6.+t*.18)),5.);
      float edge=smoothstep(0.,.18,uv.x)*smoothstep(0.,.18,1.-uv.x)*smoothstep(0.,.18,uv.y)*smoothstep(0.,.18,1.-uv.y);
      vec3 color=mix(vec3(.39,.27,.85),vec3(.27,.64,.88),uv.x);
      gl_FragColor=vec4(color,(bloom*.36+ribbon*.10)*edge);}`);
    const program=gl.createProgram(); gl.attachShader(program,vertex); gl.attachShader(program,fragment); gl.linkProgram(program);
    if (!gl.getProgramParameter(program,gl.LINK_STATUS)) throw new Error('Shader unavailable');
    gl.useProgram(program); const buffer=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
    const position=gl.getAttribLocation(program,'p'); gl.enableVertexAttribArray(position); gl.vertexAttribPointer(position,2,gl.FLOAT,false,0,0);
    const size=gl.getUniformLocation(program,'size'),time=gl.getUniformLocation(program,'t');
    let visible=false,frame=0,last=0,disposed=false;
    function draw(now){frame=0;if(disposed||!visible||document.hidden)return;
      if(now-last>45||previewMotion.matches){last=now;const rect=host.getBoundingClientRect();
        const w=Math.round(rect.width),h=Math.round(rect.height);
        if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;gl.viewport(0,0,w,h);}
        gl.uniform2f(size,w,h); gl.uniform1f(time,previewMotion.matches?0:now*.001); gl.drawArrays(gl.TRIANGLES,0,6);}
      if(!previewMotion.matches)frame=requestAnimationFrame(draw);
    }
    function resume(){cancelAnimationFrame(frame);if(!disposed)frame=requestAnimationFrame(draw);}
    const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;resume();});observer.observe(host);
    document.addEventListener('visibilitychange',resume);previewMotion.addEventListener('change',resume);
    function dispose(){disposed=true;cancelAnimationFrame(frame);observer.disconnect();document.removeEventListener('visibilitychange',resume);previewMotion.removeEventListener('change',resume);gl.deleteBuffer(buffer);gl.deleteProgram(program);gl.deleteShader(vertex);gl.deleteShader(fragment);}
    canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();dispose();canvas.remove();});
    window.addEventListener('pagehide',dispose,{once:true});
  } catch {canvas.remove();}
}
document.addEventListener('DOMContentLoaded', mountStudioLight);
