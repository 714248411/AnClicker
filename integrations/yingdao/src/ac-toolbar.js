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
  const address=document.createElement('input');address.type='text';address.value=location.href;address.title='网页地址，回车打开';
  address.style.cssText='box-sizing:border-box;width:min(260px,40vw);height:24px;padding:0 5px;font:12px system-ui;border:1px solid #cbd5e1;border-radius:4px;background:white;color:#334155;';
  panel.appendChild(address);
  const status=document.createElement('span');status.id='__rpa_navigation_status';status.setAttribute('role','status');status.style.cssText='max-width:220px;line-height:1.4;white-space:normal;color:#b45309;';panel.appendChild(status);
  let navigating=false;
  async function navigate(){
    const value=address.value.trim();
    if(!value){status.textContent='请填写完整网页地址';return;}
    address.setCustomValidity('');
    navigating=true;status.textContent='正在打开…';
    try{
      if(!window.__rpaNavigate)throw Error('地址栏连接失败，请关闭此窗口后重新打开网页');
      const result=await window.__rpaNavigate(value);
      if(!result.ok)throw Error(result.error);
      status.textContent='';address.value=result.url;
    }catch(error){status.textContent='打开失败：'+error.message;}
    finally{navigating=false;}
  }
  let zoom=Number(initialZoom)||0;
  const percent=document.createElement('span');percent.style.cssText='min-width:36px;text-align:center;font:11px system-ui;';
  const setZoom=value=>{zoom=Math.max(-3,Math.min(4,Number(value)||0));percent.textContent=Math.round(Math.pow(1.2,zoom)*100)+'%';};
  const send=action=>{if(window.__rpaSendToMain)window.__rpaSendToMain(action);};
  function button(text,title,action){const b=document.createElement('button');b.type='button';b.textContent=text;b.title=title;b.style.cssText='width:24px;height:24px;padding:0;border:1px solid #cbd5e1;border-radius:4px;background:white;color:#334155;cursor:pointer;font:12px system-ui;';b.onclick=action;panel.appendChild(b);return b;}
  button('↵','打开地址',navigate);
  button('−','缩小',()=>{setZoom(zoom-.5);send('zoom:'+zoom);});panel.appendChild(percent);
  button('+','放大',()=>{setZoom(zoom+.5);send('zoom:'+zoom);});
  button('←','后退',()=>send('back'));button('→','前进',()=>send('forward'));
  root.append(trigger,panel);document.documentElement.appendChild(root);setZoom(zoom);
  if(window.__rpaOnZoom)window.__rpaOnZoom(setZoom);
  let showTimer,hideTimer,inside=false;
  function show(){clearTimeout(showTimer);panel.hidden=false;panel.style.display='flex';trigger.style.display='none';address.value=location.href;}
  function hide(){clearTimeout(showTimer);panel.hidden=true;panel.style.display='none';trigger.style.display='block';}
  root.addEventListener('mouseenter',()=>{inside=true;clearTimeout(hideTimer);if(panel.hidden){clearTimeout(showTimer);showTimer=setTimeout(show,2000);}});
  root.addEventListener('mouseleave',()=>{inside=false;clearTimeout(showTimer);hideTimer=setTimeout(()=>{if(!navigating&&!status.textContent&&!root.contains(document.activeElement))hide();},300);});
  root.addEventListener('focusout',()=>{setTimeout(()=>{if(!inside&&!navigating&&!status.textContent&&!root.contains(document.activeElement))hide();},0);});
  root.addEventListener('keydown',e=>{if(e.key==='Escape'){document.activeElement.blur();hide();}});
  function navigationStatus(state){if(state.error){navigating=false;show();address.value=state.url;status.textContent='打开失败：'+state.error;}}
  if(window.__rpaOnNavigationStatus)window.__rpaOnNavigationStatus(navigationStatus);
  if(window.__rpaNavigationStatus)window.__rpaNavigationStatus().then(navigationStatus).catch(()=>{});
  address.addEventListener('keydown',e=>{if(e.key!=='Enter'||e.isComposing)return;e.preventDefault();e.stopPropagation();navigate();});
};
