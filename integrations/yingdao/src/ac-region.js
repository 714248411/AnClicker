'use strict';
const tableLayout=require('../../crawl4ai/table-layout.js');
function pageRegion(params, tableLayout) {
  const metrics=()=>({width:innerWidth,height:innerHeight,scrollX,scrollY,dpr:devicePixelRatio,scale:visualViewport?.scale||1,url:location.href});
  if(params.action==='geometry')return metrics();
  if(params.action==='select')return new Promise((resolve,reject)=>{
    if(globalThis.__acRegionCancel)globalThis.__acRegionCancel();
    const host=document.createElement('div');host.style.cssText='position:fixed;inset:0;z-index:2147483647;cursor:crosshair;';
    const shadow=host.attachShadow({mode:'closed'}),mask=document.createElement('div'),box=document.createElement('div'),hint=document.createElement('div');
    mask.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.12);cursor:crosshair;';
    box.style.cssText='position:fixed;border:2px solid red;background:rgba(255,0,0,.06);pointer-events:none;display:none;box-sizing:border-box;';
    hint.style.cssText='position:fixed;top:8px;left:8px;background:#222;color:white;font:14px sans-serif;padding:10px;pointer-events:none;';hint.textContent='拖动框选提取范围，Esc 取消；请勿滚动或改变窗口大小';
    shadow.append(mask,box,hint);document.documentElement.append(host);
    const before=metrics();let origin,timer;
    const cleanup=()=>{clearTimeout(timer);host.remove();document.removeEventListener('keydown',key,true);window.removeEventListener('blur',cancel);delete globalThis.__acRegionCancel;};
    const cancel=()=>{cleanup();reject(new Error('已取消网页区域框选'));};
    const key=e=>{if(e.key==='Escape'){e.preventDefault();e.stopImmediatePropagation();cancel();}};
    globalThis.__acRegionCancel=cancel;document.addEventListener('keydown',key,true);window.addEventListener('blur',cancel);
    mask.addEventListener('wheel',e=>e.preventDefault(),{passive:false});
    mask.addEventListener('pointerdown',e=>{if(e.button!==0)return;e.preventDefault();origin={x:e.clientX,y:e.clientY};mask.setPointerCapture(e.pointerId);});
    mask.addEventListener('pointermove',e=>{if(!origin)return;Object.assign(box.style,{display:'block',left:Math.min(origin.x,e.clientX)+'px',top:Math.min(origin.y,e.clientY)+'px',width:Math.abs(origin.x-e.clientX)+'px',height:Math.abs(origin.y-e.clientY)+'px'});});
    mask.addEventListener('pointerup',e=>{if(!origin)return;const x=Math.max(0,Math.min(origin.x,e.clientX)),y=Math.max(0,Math.min(origin.y,e.clientY));const right=Math.min(innerWidth,Math.max(origin.x,e.clientX)),bottom=Math.min(innerHeight,Math.max(origin.y,e.clientY));cleanup();if(right-x<4||bottom-y<4){reject(new Error('框选范围太小，请重新框选'));return;}if(JSON.stringify(before)!==JSON.stringify(metrics())){reject(new Error('网页位置或大小已变化，请重新框选'));return;}resolve({...before,x,y,w:right-x,h:bottom-y});});
    timer=setTimeout(cancel,120000);
  });
  const r=params.region,current=metrics();
  if(!r||!['x','y','w','h','width','height','scrollX','scrollY','dpr','scale'].every(k=>Number.isFinite(r[k])))throw new Error('请先框选网页区域');
  if(r.url!==current.url||['width','height','scrollX','scrollY','dpr','scale'].some(k=>Math.abs(current[k]-r[k])>.5))throw new Error('网页地址、大小、缩放或滚动位置已变化，请恢复原位置或重新框选');
  if(r.w<4||r.h<4||r.x<0||r.y<0||r.x+r.w>innerWidth+.5||r.y+r.h>innerHeight+.5)throw new Error('框选区域超出当前网页视野');
  const overlaps=b=>b.width>0&&b.height>0&&b.right>r.x&&b.left<r.x+r.w&&b.bottom>r.y&&b.top<r.y+r.h;
  const inside=b=>overlaps(b)&&b.left>=r.x&&b.right<=r.x+r.w&&b.top>=r.y&&b.bottom<=r.y+r.h;
  const visible=el=>{const s=getComputedStyle(el);return s.display!=='none'&&s.visibility==='visible'&&Number(s.opacity)!==0;};
  for(const el of document.querySelectorAll('iframe,frame,canvas,video'))if(visible(el)&&overlaps(el.getBoundingClientRect()))throw new Error('区域包含嵌入网页、画布或视频，无法可靠提取文本，请避开这些内容或使用截图OCR');
  const hit=(el,b)=>{const x=Math.max(r.x,Math.min(r.x+r.w,(b.left+b.right)/2)),y=Math.max(r.y,Math.min(r.y+r.h,(b.top+b.bottom)/2));const top=document.elementFromPoint(x,y);return top&&(top===el||el.contains(top));};
  const limit=params.maxChars||20000,parts=[],layoutItems=[];let count=0,truncated=false,examined=0;
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);const range=document.createRange();let node;
  while((node=walker.nextNode())){
    const el=node.parentElement;if(!el||el.closest('script,style,noscript,input,textarea,select')||!visible(el)||!node.textContent.trim())continue;
    range.selectNodeContents(node);if(!Array.from(range.getClientRects()).some(overlaps))continue;
    let piece='',line=null;
    const flushLine=()=>{if(line&&line.text.trim())layoutItems.push(line);line=null;};
    const fontSize=parseFloat(getComputedStyle(el).fontSize)||14;
    for(let i=0;i<node.length;i++){
      if(++examined>500000||count>=limit){truncated=true;break;}
      range.setStart(node,i);range.setEnd(node,i+1);
      const b=range.getBoundingClientRect();if(overlaps(b)&&b.left+b.width/2>=r.x&&b.left+b.width/2<=r.x+r.w&&b.top+b.height/2>=r.y&&b.top+b.height/2<=r.y+r.h&&document.elementFromPoint((b.left+b.right)/2,(b.top+b.bottom)/2)===el){
        piece+=node.textContent[i];count++;
        if(line&&(Math.abs(line.y-(b.top-r.y))>2||b.left-r.x>line.x+line.w+3))flushLine();
        if(!line)line={text:'',x:Math.max(0,b.left-r.x),y:Math.max(0,b.top-r.y),w:0,h:b.height,fontSize};
        line.text+=node.textContent[i];line.w=Math.min(r.w,b.right-r.x)-line.x;line.h=Math.max(line.h,b.height);
      }
    }
    flushLine();
    if(piece.trim())parts.push(piece.trim());if(truncated)break;
  }
  const selected=selector=>Array.from(document.querySelectorAll(selector)).filter(el=>visible(el)&&inside(el.getBoundingClientRect())&&hit(el,el.getBoundingClientRect())).slice(0,100);
  const text=parts.join('\n');
  return {url:location.href,title:document.title,text,markdown:text,layout:{width:r.w,height:r.h,items:layoutItems},
    links:selected('a[href]').filter(el=>/^https?:/.test(el.href)).map(el=>({url:el.href,text:el.innerText})),
    images:selected('img').filter(el=>/^https?:/.test(el.currentSrc||el.src)).map(el=>({url:el.currentSrc||el.src,alt:el.alt})),
    tables:selected('table').slice(0,20).map(table=>{
      const layout=tableLayout(table),trs=Array.from(table.rows).filter(row=>row.closest('table')===table).slice(0,100);
      const rows=Array.from({length:trs.length},()=>Array(layout?.columns.length||0).fill(''));
      if(layout){let index=0;trs.forEach((row,r)=>Array.from(row.cells).slice(0,50).forEach(cell=>{
        const spec=layout.cells[index];if(!spec||spec.row!==r)return;index++;
        for(let y=r;y<r+spec.rowspan;y++)for(let x=spec.col;x<spec.col+spec.colspan;x++)rows[y][x]=cell.innerText;
      }));}else trs.forEach((row,r)=>rows[r]=Array.from(row.cells).slice(0,50).map(cell=>cell.innerText));
      const header=trs[0]?.querySelector('th')&&!trs[0]?.querySelector('td');
      return {caption:table.caption?.innerText||'',headers:header?rows.shift():[],rows,layout};
    }),
    titles:{title:document.title,headings:selected('h1,h2,h3,h4,h5,h6').map(el=>({level:Number(el.tagName[1]),text:el.innerText}))},truncated};
}
async function execute(wc,params){
  if(!wc||wc.isDestroyed())throw new Error('请先在 AnClicker 内打开网页');
  if(!params||!['select','extract','geometry'].includes(params.action))throw new Error('未知区域操作');
  if(!/^https?:/.test(wc.getURL()))throw new Error('请选择普通网页');
  const clean={action:params.action,region:params.region,maxChars:params.maxChars};
  if(params.action==='extract'&&(!Number.isInteger(params.maxChars)||params.maxChars<500||params.maxChars>200000))throw new Error('最大字符数必须为500到200000');
  const result=await wc.executeJavaScriptInIsolatedWorld(1003,[{code:'(async()=>{try{return {ok:true,result:await ('+pageRegion.toString()+')('+JSON.stringify(clean)+','+tableLayout.toString()+')}}catch(e){return {ok:false,error:String(e.message||e)}}})()'}],true);
  if(!result.ok)throw new Error(result.error);return result.result;
}
module.exports={execute,pageRegion};
