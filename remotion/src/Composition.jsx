import React, {useLayoutEffect, useRef, useState} from 'react';
import {AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {stateAt} from './motion.mjs';

const families = {sans: 'Arial, sans-serif', serif: 'Georgia, serif', mono: 'Consolas, monospace'};

function Text({track, state, height, width, boxHeight}) {
  const ref = useRef(null);
  const [size, setSize] = useState(track.size * height);
  // Measure the complete string so a typing reveal never changes its font size.
  useLayoutEffect(() => {
    const element = ref.current;
    const intended = track.size * height;
    element.style.fontSize = `${intended}px`;
    setSize(Math.max(2, intended * Math.min(1, width / Math.max(1, element.scrollWidth), boxHeight / Math.max(1, element.scrollHeight))));
  }, [track.text, track.size, track.font, track.weight, height, width, boxHeight]);
  const common = {fontFamily: families[track.font], fontWeight: track.weight === 'bold' ? 700 : 400,
    whiteSpace: 'pre', lineHeight: 1.18, textAlign: track.align};
  return <>
    <span ref={ref} style={{...common, position:'absolute', visibility:'hidden', fontSize:track.size*height}}>{track.text}</span>
    <span style={{...common, fontSize:size}}>{track.text.slice(0, Math.ceil(track.text.length * state.reveal))}</span>
  </>;
}

function Layer({track, time, logo}) {
  const {width, height} = useVideoConfig();
  if (time < track.start || time >= track.end) return null;
  const state = stateAt(track, time), w = state.w * width, h = state.h * height;
  const style = {position:'absolute', left:state.x*width, top:state.y*height, width:w, height:h,
    opacity:state.opacity, transform:`rotate(${state.rotation}deg)`, filter:state.blur ? `blur(${state.blur}px)` : undefined,
    color:track.color, boxSizing:'border-box', display:'flex', alignItems:'center',
    justifyContent:{left:'flex-start', center:'center', right:'flex-end'}[track.align]};
  const paint = {width:'100%', height:'100%', boxSizing:'border-box',
    clipPath:track.kind !== 'text' ? `inset(0 ${(1-state.reveal)*100}% 0 0)` : undefined};
  let content;
  if (track.kind === 'text') content = <Text track={track} state={state} height={height} width={w} boxHeight={h}/>;
  else if (track.kind === 'image') content = logo && track.asset === 'logo' ? <Img src={staticFile(logo)} style={{...paint, objectFit:'contain'}}/> : null;
  else if (track.kind === 'line') content = <svg width={w} height={h} style={paint}><line x1="0" y1="0" x2={w} y2={h} stroke={track.color} strokeWidth={Math.max(1,track.stroke*height)}/></svg>;
  else content = <div style={{...paint, borderRadius:track.kind==='ellipse'?'50%':track.radius*height,
    background:track.kind==='gradient'?`linear-gradient(${track.color},${track.color2})`:track.stroke?'transparent':track.color,
    border:track.stroke?`${track.stroke*height}px solid ${track.color}`:undefined}}/>;
  return <div style={style}>{content}</div>;
}

export function MotionComposition({plan, audio, logo}) {
  const frame = useCurrentFrame(), {fps} = useVideoConfig();
  return <AbsoluteFill style={{backgroundColor:plan.background, overflow:'hidden'}}>
    {audio ? <Audio src={staticFile(audio)}/> : null}
    {plan.tracks.map((track, index) => <Layer key={`${index}-${track.id}`} track={track} time={frame/fps} logo={logo}/>)}
  </AbsoluteFill>;
}
