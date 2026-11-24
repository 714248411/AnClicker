'use strict';
const tasks=new WeakMap();
function transient(error){return /ECONNRESET|ECONNREFUSED|ETIMEDOUT|EPIPE|ERR_CONNECTION_(RESET|CLOSED|REFUSED|ABORTED)|ERR_EMPTY_RESPONSE|ERR_NETWORK_CHANGED|ERR_INTERNET_DISCONNECTED|ERR_TIMED_OUT/.test(String(error&&error.message||error));}
function cancelled(){const error=Error('已取消网页重连');error.code='NAVIGATION_REPLACED';return error;}
async function recover(page,url,navigate,report){
 const prior=tasks.get(page);if(prior)prior.cancel();
 let stopped=false,wake=null;
 const task={cancel(){stopped=true;if(wake)wake();}};tasks.set(page,task);
 const stop=()=>task.cancel();page.once('destroyed',stop);
 try{
  for(let attempt=0;attempt<4;attempt++){
   if(stopped||page.isDestroyed())throw cancelled();
   try{return await navigate(page,url);}
   catch(error){
    if(stopped||error.code==='NAVIGATION_REPLACED')throw cancelled();
    if(!transient(error)||attempt===3){report(error,'navigation',page);throw error;}
    const retry=Error('网络连接中断，正在自动重连（'+(attempt+1)+'/3）：'+error.message);retry.stack=error.stack;
    report(retry,'navigation-retry',page);
    await new Promise(resolve=>{const timer=setTimeout(done,500*2**attempt);function done(){clearTimeout(timer);wake=null;resolve();}wake=done;});
   }
  }
 }finally{page.removeListener('destroyed',stop);if(tasks.get(page)===task){tasks.delete(page);page.emit('ac:recovery-finished');}}
}
function cancel(page){const task=tasks.get(page);if(task)task.cancel();}
module.exports={recover,cancel,transient};
