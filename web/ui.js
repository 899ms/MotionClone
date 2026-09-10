// Original local SVG assets. User text is always inserted as text, never HTML.
function icon(name, extraClass='') {
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('class','icon '+extraClass);svg.setAttribute('aria-hidden','true');
  svg.setAttribute('focusable','false');
  const use=document.createElementNS(svg.namespaceURI,'use');
  use.setAttribute('href','/static/assets/icons.svg#'+name);svg.append(use);return svg;
}
function setControl(id,text,name) {
  const element=typeof id==='string'?document.getElementById(id):id;
  const label=document.createElement('span');label.textContent=text;
  element.replaceChildren(icon(name||element.dataset.icon||'arrow-right'),label);
}
function decorateControls(root=document) {
  root.querySelectorAll('[data-icon]').forEach(element=>{
    if(!element.querySelector(':scope > svg.icon'))element.prepend(icon(element.dataset.icon));
  });
}
document.addEventListener('DOMContentLoaded',()=>decorateControls());
