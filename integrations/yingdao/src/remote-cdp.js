// Connect to already-running local CDP browsers; never launch or close them.
const http = require('http');
const WebSocket = require('ws');
function endpointUrl(value) {
  const url = new URL(value);
  if (url.protocol !== 'http:' || !['127.0.0.1','localhost','[::1]'].includes(url.hostname) || !url.port || url.username || url.password) throw Error('仅支持本机 CDP 地址');
  return url.origin;
}
function getPages(endpoint) {
  return new Promise((resolve,reject)=>{
    const req=http.get(endpointUrl(endpoint)+'/json/list',res=>{
      let data='';
      res.on('data',chunk=>{data+=chunk;if(data.length>4*1024*1024)req.destroy(Error('CDP 页面列表过大'));});
      res.on('end',()=>{try{if(res.statusCode!==200)throw Error('CDP HTTP '+res.statusCode);const pages=JSON.parse(data);if(!Array.isArray(pages))throw Error('CDP 列表格式无效');resolve(pages.filter(p=>p.type==='page'&&p.webSocketDebuggerUrl));}catch(e){reject(e);}});
      res.on('error',reject);
    });
    req.setTimeout(1500,()=>req.destroy(Error('CDP 连接超时')));req.on('error',reject);
  });
}
async function list(endpoints) {
  const sources=[...new Map((endpoints||[]).slice(0,32).map(p=>[p.endpoint,p])).values()];
  const groups=await Promise.all(sources.map(async source=>{
    try{return (await getPages(source.endpoint)).map(p=>({id:p.id,url:p.url,title:p.title,remote:true,endpoint:endpointUrl(source.endpoint),engine:'外部 CDP',badge:(source.browser||'浏览器')+' · '+new URL(source.endpoint).port,session:endpointUrl(source.endpoint)}));}
    catch(_){return [];}
  }));return groups.flat();
}
async function connect(target) {
  const endpoint=endpointUrl(target.endpoint);
  const pages=await getPages(endpoint);
  let page=pages.find(p=>p.id===target.id);
  if(!page){const matches=pages.filter(p=>target.url&&p.url===target.url);if(matches.length===1)page=matches[0];}
  if(!page)throw Error('外部网页已关闭或目标不唯一，请刷新窗口后重新选择');
  const address=new URL(page.webSocketDebuggerUrl),base=new URL(endpoint);
  if(address.protocol!=='ws:' || !['127.0.0.1','localhost','[::1]'].includes(address.hostname) || address.port!==base.port)throw Error('外部 CDP 返回了不匹配的连接地址');
  const socket=new WebSocket(address.href,{handshakeTimeout:3000,maxPayload:16*1024*1024});
  let sequence=0;const pending=new Map();
  const fail=error=>{for(const item of pending.values()){clearTimeout(item.timer);item.reject(error);}pending.clear();};
  socket.on('error',fail);socket.on('close',()=>fail(Error('外部 CDP 连接已关闭')));
  socket.on('message',raw=>{let m;try{m=JSON.parse(raw);}catch(_){return;}const p=pending.get(m.id);if(!p)return;pending.delete(m.id);clearTimeout(p.timer);if(m.error)p.reject(Error(m.error.message));else p.resolve(m.result||{});});
  await new Promise((resolve,reject)=>{socket.once('open',resolve);socket.once('error',reject);});
  return {
    alive:()=>socket.readyState===WebSocket.OPEN,
    close:()=>socket.close(),
    send(method,params={}){return new Promise((resolve,reject)=>{
      const id=++sequence;
      const timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP 指令超时：'+method));},10000);
      pending.set(id,{resolve,reject,timer});
      socket.send(JSON.stringify({id,method,params}),error=>{if(error){clearTimeout(timer);pending.delete(id);reject(error);}});
    });},
    async evaluate(expression){const r=await this.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true,userGesture:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.text||'网页执行失败');return r.result&&r.result.value;}
  };
}
async function withTarget(target, work){const client=await connect(target);try{return await work(client);}finally{client.close();}}
module.exports={list,connect,withTarget,endpointUrl};
