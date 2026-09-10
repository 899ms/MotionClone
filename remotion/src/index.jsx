import React from 'react';
import {Composition, registerRoot, delayRender, continueRender, cancelRender, staticFile} from 'remotion';
import {MotionComposition} from './Composition.jsx';

function Root() {
  const [handle] = React.useState(() => delayRender('Loading saved motion'));
  const [project, setProject] = React.useState(null);
  React.useEffect(() => {
    fetch(staticFile('project.json')).then(r => {if (!r.ok) throw new Error('Project not found'); return r.json();})
      .then(data => {setProject(data);continueRender(handle);}).catch(cancelRender);
  }, [handle]);
  if (!project) return null;
  return <Composition id="Motion" component={MotionComposition} width={project.media.width}
    height={project.media.height} fps={project.media.fps}
    durationInFrames={Math.ceil(project.media.duration*project.media.fps)} defaultProps={project}
    calculateMetadata={({props}) => ({width:props.media.width, height:props.media.height,
      fps:props.media.fps, durationInFrames:Math.ceil(props.media.duration*props.media.fps)})}/>;
}
registerRoot(Root);
