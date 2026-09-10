import {bundle} from '@remotion/bundler';
import {selectComposition, renderMedia, makeCancelSignal} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const projectFile = path.resolve(process.argv[2] || path.join(root,'public/project.json'));
const destination = path.resolve(process.argv[3] || path.join(root,'out/video.mp4'));
const preview = process.argv.includes('--preview');
const project = JSON.parse(fs.readFileSync(projectFile,'utf8'));
const publicDir = path.dirname(projectFile);
const bundleDir = path.join(root,'.bundle');
const signature = ['package-lock.json','src/index.jsx','src/Composition.jsx','src/motion.mjs']
  .map(f => fs.existsSync(path.join(root,f)) ? fs.readFileSync(path.join(root,f),'utf8') : '').join('\n');
const {createHash} = await import('node:crypto');
const stamp = createHash('sha256').update(signature).digest('hex');
const stampFile = path.join(bundleDir,'.signature');
if (!fs.existsSync(stampFile) || fs.readFileSync(stampFile,'utf8') !== stamp) {
  await bundle({entryPoint:path.join(root,'src/index.jsx'), outDir:bundleDir, publicDir:path.join(root,'public')});
  fs.writeFileSync(stampFile, stamp);
}
// The app runs one render at a time. Only fixed, validated asset names are staged.
const staticDir = path.join(bundleDir,'public');
fs.mkdirSync(staticDir,{recursive:true});
for (const name of ['project.json','audio.m4a','logo.png']) {
  const source = path.join(publicDir,name), target=path.join(staticDir,name);
  if (fs.existsSync(source)) fs.copyFileSync(source,target);
  else if (fs.existsSync(target)) fs.unlinkSync(target);
}
const browsers = [process.env.REMOTION_BROWSER, 'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'];
const browserExecutable = browsers.find(p => p && fs.existsSync(p));
const composition = await selectComposition({serveUrl:bundleDir,id:'Motion',inputProps:project,browserExecutable});
const {cancelSignal,cancel} = makeCancelSignal();
const cancelFile = process.env.FRAMEFORGE_CANCEL_FILE;
const timer = cancelFile ? setInterval(() => {if(fs.existsSync(cancelFile)) cancel();},200) : null;
fs.mkdirSync(path.dirname(destination),{recursive:true});
try {
  await renderMedia({serveUrl:bundleDir,composition,inputProps:project,outputLocation:destination,
    codec:'h264',crf:preview?24:18,concurrency:2,browserExecutable,cancelSignal,muted:!project.audio,
    scale:preview?Math.min(1,960/composition.width):1,
    onProgress:({progress}) => process.stdout.write(JSON.stringify({progress:Math.round(progress*100)})+'\n')});
} finally {if(timer) clearInterval(timer);}
