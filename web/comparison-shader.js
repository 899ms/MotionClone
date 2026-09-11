// Original WebGL light-field material. DOM and video surfaces stay above it.
(() => {
  const stage=document.getElementById('comparison-stage');
  if(!stage)return;
  const canvas=document.createElement('canvas');
  const surface=document.getElementById('recording-canvas')||stage;
  canvas.id='promo-shader';canvas.setAttribute('aria-hidden','true');surface.prepend(canvas);
  let gl;
  try{gl=canvas.getContext('webgl',{alpha:true,antialias:false,depth:false,powerPreference:'low-power'});}catch{}
  if(!gl){canvas.dataset.state='fallback';return;}
  let program,buffer,vertex,fragment;
  const dispose=()=>{
    if(program)gl.deleteProgram(program);if(buffer)gl.deleteBuffer(buffer);
    if(vertex)gl.deleteShader(vertex);if(fragment)gl.deleteShader(fragment);
  };
  try{
    const compile=(type,code)=>{
      const shader=gl.createShader(type);gl.shaderSource(shader,code);gl.compileShader(shader);
      if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS)){gl.deleteShader(shader);throw new Error('Shader unavailable');}
      return shader;
    };
    vertex=compile(gl.VERTEX_SHADER,'attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}');
    fragment=compile(gl.FRAGMENT_SHADER,`
      precision mediump float;
      uniform vec2 resolution;
      uniform float time;
      void main(){
        vec2 uv=gl_FragCoord.xy/resolution;
        vec2 p=vec2(uv.x,1.-uv.y);
        float t=time*.075;
        float crest=.075+.055*sin(p.x*5.5+t)+.045*cos(p.x*9.-t*.6);
        float d=abs(p.y-crest);
        float ribbon=exp(-d*27.)*.20+exp(-d*110.)*.16;
        float ridges=.5+.5*sin(d*200.-p.x*8.+t);
        float top=exp(-p.y*7.);
        float glow=exp(-length((p-vec2(.63+.1*sin(t),-.03))*vec2(1.7,2.4))*3.);
        float edge=exp(-p.x*11.)*exp(-abs(p.y-.72)*4.);
        vec3 violet=vec3(.44,.25,.82);
        vec3 color=violet*(ribbon*(.6+.4*ridges)+glow*.28);
        color+=vec3(.16,.38,.49)*edge*.16;
        color+=vec3(.60,.45,.83)*pow(max(0.,1.-d*90.),3.)*.055;
        float grain=fract(sin(dot(gl_FragCoord.xy,vec2(12.9898,78.233)))*43758.5453);
        color+=(grain-.5)*.014;
        gl_FragColor=vec4(color,(top*.72+edge*.2)*.9);
      }
    `);
    program=gl.createProgram();gl.attachShader(program,vertex);gl.attachShader(program,fragment);gl.linkProgram(program);
    if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw new Error('Shader unavailable');
    gl.useProgram(program);buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
    const position=gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(position);gl.vertexAttribPointer(position,2,gl.FLOAT,false,0,0);
  }catch{dispose();canvas.dataset.state='fallback';return;}
  const resolution=gl.getUniformLocation(program,'resolution'),time=gl.getUniformLocation(program,'time');
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const capture=new URLSearchParams(location.search).get('capture')==='1';
  let raf=0,last=0,elapsed=0,visible=false,stopped=false,count=0;
  const eligible=()=>!stopped&&visible&&!document.hidden&&stage.classList.contains('promo-active')&&(!stage.dataset.look||stage.dataset.look==='studio');
  function draw(){
    const box=surface.getBoundingClientRect();
    const scale=Math.min(devicePixelRatio||1,1.25,1400/Math.max(1,box.width),1000/Math.max(1,box.height));
    const w=Math.max(1,Math.round(box.width*scale)),h=Math.max(1,Math.round(box.height*scale));
    if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;gl.viewport(0,0,w,h);}
    gl.uniform2f(resolution,w,h);gl.uniform1f(time,elapsed/1000);gl.drawArrays(gl.TRIANGLES,0,6);
    canvas.dataset.frames=String(++count);
  }
  function tick(now){
    raf=0;if(!eligible())return;
    if(now-last>=40){elapsed+=Math.min(now-last,80);last=now;draw();}
    raf=requestAnimationFrame(tick);
  }
  function refresh(){
    cancelAnimationFrame(raf);raf=0;last=performance.now();
    if(!eligible()){canvas.dataset.state=stopped?'fallback':'paused';return;}
    canvas.dataset.state=reduced.matches||capture?'static':'running';draw();
    if(!reduced.matches&&!capture)raf=requestAnimationFrame(tick);
  }
  window.seekComparisonShader=t=>{if(capture&&eligible()){elapsed=t*1000;draw();}};
  const intersection=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;refresh();});intersection.observe(stage);
  const resize=new ResizeObserver(refresh);resize.observe(stage);
  const mutation=new MutationObserver(refresh);mutation.observe(stage,{attributes:true,attributeFilter:['class','data-look','data-format']});
  document.addEventListener('visibilitychange',refresh);reduced.addEventListener('change',refresh);
  const lost=event=>{event.preventDefault();stopped=true;refresh();canvas.style.visibility='hidden';};
  canvas.addEventListener('webglcontextlost',lost);
  window.addEventListener('pagehide',()=>{
    stopped=true;cancelAnimationFrame(raf);intersection.disconnect();resize.disconnect();mutation.disconnect();
    document.removeEventListener('visibilitychange',refresh);reduced.removeEventListener('change',refresh);
    canvas.removeEventListener('webglcontextlost',lost);dispose();gl.getExtension('WEBGL_lose_context')?.loseContext();
  },{once:true});
})();
