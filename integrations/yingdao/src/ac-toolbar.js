'use strict';
// Runs in the page; keep the implementation self-contained for executeJavaScript.
module.exports = function installToolbar(initialZoom) {
  if (document.getElementById('__rpa_toolbar')) return;
  const root=document.createElement('div');root.id='__rpa_toolbar';
  root.style.cssText='position:fixed;top:6px;right:6px;z-index:2147483646;font:12px/1 system-ui;color:#334155;';
  const trigger=document.createElement('button');trigger.id='__rpa_toolbar_trigger';
  trigger.textContent='⋯';trigger.title='停留2秒展开网页工具栏';
  trigger.style.cssText='display:block;margin-left:auto;width:28px;height:22px;padding:0;border:1px solid #cbd5e1;border-radius:5px;background:#f8fafcbd;color:#64748b;cursor:default;';
  const panel=document.createElement('div');panel.id='__rpa_toolbar_panel';panel.hidden=true;
  panel.style.cssText='display:none;align-items:center;gap:3px;padding:3px;border:1px solid #cbd5e1;border-radius:6px;background:#f8fafcf2;box-shadow:0 2px 8px #0002;';
  const address=document.createElement('input');address.type='url';address.value=location.href;address.title='网页地址，回车打开';
  address.style.cssText='box-sizing:border-box;width:min(260px,40vw);height:24px;padding:0 5px;font:12px system-ui;border:1px solid #cbd5e1;border-radius:4px;background:white;color:#334155;';
  panel.appendChild(address);
  let zoom=Number(initialZoom)||0;
  const percent=document.createElement('span');percent.style.cssText='min-width:36px;text-align:center;font:11px system-ui;';
  const setZoom=value=>{zoom=Math.max(-3,Math.min(4,Number(value)||0));percent.textContent=Math.round(Math.pow(1.2,zoom)*100)+'%';};
  const send=action=>{if(window.__rpaSendToMain)window.__rpaSendToMain(action);};
  function button(text,title,action){const b=document.createElement('button');b.type='button';b.textContent=text;b.title=title;b.style.cssText='width:24px;height:24px;padding:0;border:1px solid #cbd5e1;border-radius:4px;background:white;color:#334155;cursor:pointer;font:12px system-ui;';b.onclick=action;panel.appendChild(b);return b;}
  button('−','缩小',()=>{setZoom(zoom-.5);send('zoom:'+zoom);});panel.appendChild(percent);
  button('+','放大',()=>{setZoom(zoom+.5);send('zoom:'+zoom);});
  button('←','后退',()=>send('back'));button('→','前进',()=>send('forward'));
  root.append(trigger,panel);document.documentElement.appendChild(root);setZoom(zoom);
  if(window.__rpaOnZoom)window.__rpaOnZoom(setZoom);
  let showTimer,hideTimer,inside=false;
  function show(){clearTimeout(showTimer);panel.hidden=false;panel.style.display='flex';trigger.style.display='none';address.value=location.href;}
  function hide(){clearTimeout(showTimer);panel.hidden=true;panel.style.display='none';trigger.style.display='block';}
  root.addEventListener('mouseenter',()=>{inside=true;clearTimeout(hideTimer);if(panel.hidden){clearTimeout(showTimer);showTimer=setTimeout(show,2000);}});
  root.addEventListener('mouseleave',()=>{inside=false;clearTimeout(showTimer);hideTimer=setTimeout(()=>{if(!root.contains(document.activeElement))hide();},300);});
  root.addEventListener('focusout',()=>{setTimeout(()=>{if(!inside&&!root.contains(document.activeElement))hide();},0);});
  root.addEventListener('keydown',e=>{if(e.key==='Escape'){document.activeElement.blur();hide();}});
  address.addEventListener('keydown',e=>{if(e.key!=='Enter')return;e.preventDefault();let value=address.value.trim();if(!value)return;if(!/^[a-z]+:/i.test(value))value='https://'+value;try{const parsed=new URL(value);if(['http:','https:'].includes(parsed.protocol))send('navigate:'+parsed.href);}catch(_){address.setCustomValidity('请输入有效网页地址');address.reportValidity();}});
};
