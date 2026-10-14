'use strict';
// Runs in an isolated world: page scripts cannot replace the element reference map.
function pageAgent(params) {
  const visible = el => {
    const r = el.getBoundingClientRect(), style = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
  };
  const selector = el => {
    if (el.id && document.querySelectorAll('#'+CSS.escape(el.id)).length===1) return '#'+CSS.escape(el.id);
    const parts=[];
    for(let current=el; current && current.nodeType===1 && parts.length<20; current=current.parentElement) {
      const tag=current.tagName.toLowerCase();
      const siblings=current.parentElement ? Array.from(current.parentElement.children).filter(x=>x.tagName===current.tagName) : [current];
      parts.unshift(tag+(siblings.length>1?':nth-of-type('+(siblings.indexOf(current)+1)+')':''));
    }
    return parts.join(' > ');
  };
  const summarize = el => ({tag:el.tagName.toLowerCase(), type:el.type||'',
    label:String(el.getAttribute('aria-label')||el.innerText||el.getAttribute('placeholder')||el.getAttribute('title')||el.name||'').trim().slice(0,120),
    selector:selector(el)});
  if (params.action==='observe') {
    const token=String(params.token), items=[], refs=new Map();
    for(const el of document.querySelectorAll('a[href],button,input:not([type=hidden]),textarea,select,[role=button],[role=link],[contenteditable=true]')) {
      if(items.length>=80)break;
      if(!visible(el)||el.disabled||el.type==='password'||el.type==='file')continue;
      const rect=el.getBoundingClientRect();
      if(rect.bottom<=0||rect.top>=innerHeight||rect.right<=0||rect.left>=innerWidth)continue;
      const ref=token+'-'+(items.length+1);
      refs.set(ref,{el,description:summarize(el)});
      items.push({ref,...summarize(el)});
    }
    globalThis.__acAgent={refs,url:location.href};
    // Only rendered text is shared, never input values, hidden fields, HTML or cookies.
    return {url:location.href,title:document.title,text:(document.body?.innerText||'').slice(0,6000),elements:items};
  }
  const state=globalThis.__acAgent;
  if(!state||state.url!==location.href)throw new Error('页面已变化，请重新查看页面');
  if(params.action==='scroll') {
    window.scrollBy(0,params.direction==='up'?-600:600);
    state.refs.clear();return {action:'scroll',direction:params.direction};
  }
  const entry=state.refs.get(params.ref);
  if(!entry||!entry.el.isConnected||!visible(entry.el)||entry.el.disabled)throw new Error('元素已失效，请重新查看页面');
  const el=entry.el;
  if(JSON.stringify(summarize(el))!==JSON.stringify(entry.description))throw new Error('元素内容已变化，请重新查看页面');
  const result={action:params.action,...entry.description};
  el.scrollIntoView({block:'center'});
  const rect=el.getBoundingClientRect();
  const hit=document.elementFromPoint(Math.max(0,Math.min(innerWidth-1,rect.left+rect.width/2)),Math.max(0,Math.min(innerHeight-1,rect.top+rect.height/2)));
  if(!hit || (hit!==el && !el.contains(hit)))throw new Error('元素被遮挡，请重新查看页面或先关闭遮挡层');
  if(params.action==='click') {
    if(el.type==='password'||el.type==='file')throw new Error('请手动操作密码或文件控件');
    el.click();
  } else if(params.action==='type') {
    if(!['INPUT','TEXTAREA'].includes(el.tagName)||['password','file','hidden','submit','button','checkbox','radio'].includes(el.type))throw new Error('请选择普通文本输入框，密码请手动输入');
    if(el.readOnly)throw new Error('输入框只读');
    const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto,'value').set.call(el,params.text);
    el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));el.focus();
    result.text=params.text;
  } else throw new Error('不支持的 Agent 操作');
  state.refs.clear();
  return result;
}

let sequence=0;
async function execute(wc, params) {
  if(!wc||wc.isDestroyed())throw new Error('请先让 Agent 打开一个网页');
  if(!params||!['observe','click','type','scroll'].includes(params.action))throw new Error('未知 Agent 操作');
  const clean={action:params.action};
  if(params.action==='observe')clean.token='p'+(++sequence);
  if(['click','type'].includes(params.action)) {
    if(typeof params.ref!=='string'||!/^p\d+-\d+$/.test(params.ref))throw new Error('元素编号无效');
    clean.ref=params.ref;
  }
  if(params.action==='type') {
    if(typeof params.text!=='string'||params.text.length>4000)throw new Error('输入内容最多 4000 字');
    clean.text=params.text;
  }
  if(params.action==='scroll') {
    if(!['up','down'].includes(params.direction))throw new Error('滚动方向无效');
    clean.direction=params.direction;
  }
  let timer;
  try {
    const response = await Promise.race([
      wc.executeJavaScriptInIsolatedWorld(1002,[{code:'(()=>{try{return {ok:true,result:('+pageAgent.toString()+')('+JSON.stringify(clean)+')}}catch(error){return {ok:false,error:String(error.message||error)}}})()'}],true),
      new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('读取网页超时，请重试')),10000);})
    ]);
    if(!response.ok)throw new Error(response.error);
    return response.result;
  } finally {clearTimeout(timer);}
}
module.exports={execute,pageAgent};
