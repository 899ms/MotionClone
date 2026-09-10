import {test} from 'node:test';
import assert from 'node:assert/strict';
import {stateAt} from '../src/motion.mjs';

test('motion is continuous and clamps outside keyframes',()=>{
  const track={easing:'linear',keyframes:[{t:1,x:0,opacity:0},{t:3,x:1,opacity:1}]};
  assert.equal(stateAt(track,0).x,0);
  assert.equal(stateAt(track,2).x,.5);
  assert.equal(stateAt(track,4).opacity,1);
});
test('step holds and cubic ease-out advances toward the target',()=>{
  const keyframes=[{t:0,x:0},{t:1,x:1}];
  assert.equal(stateAt({keyframes,easing:'step'},.9).x,0);
  assert.equal(stateAt({keyframes,easing:'out'},.5).x,.875);
  assert.equal(stateAt({keyframes,easing:'step'},1).x,1);
});
