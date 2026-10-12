'use strict';
const active=new WeakMap();
module.exports=function navigate(page,url,timeoutMs=30000){
  const previous=active.get(page);
  if(previous)previous.cancel();
  return new Promise((resolve,reject)=>{
    let finished=false, committed=false, timer, readyTimer;
    const listeners=[];
    const state={requestedUrl:url,url:page.getURL(),loading:true,error:''};
    function publish(change){Object.assign(state,change);page.__acNavigationStatus={...state};page.emit('ac:navigation-state',{...state});}
    function cleanup(){clearTimeout(timer);clearTimeout(readyTimer);for(const [event,fn] of listeners)page.removeListener(event,fn);if(active.get(page)===task)active.delete(page);}
    function finish(error){
      if(finished)return;finished=true;cleanup();
      if(error){if(error.code!=='NAVIGATION_REPLACED')publish({loading:false,error:error.message});reject(error);}
      else{const actual=page.getURL();publish({url:actual,loading:false,error:''});resolve(actual);}
    }
    function listen(event,fn){page.on(event,fn);listeners.push([event,fn]);}
    const task={cancel(){const error=Error('已切换到新的网页地址');error.code='NAVIGATION_REPLACED';finish(error);}};
    active.set(page,task);
    listen('did-start-navigation',(_e,_url,inPlace,isMain)=>{if(isMain&&!inPlace){committed=false;clearTimeout(readyTimer);}});
    listen('did-navigate',()=>{committed=true;});
    listen('dom-ready',()=>{if(committed){clearTimeout(readyTimer);readyTimer=setTimeout(()=>finish(),600);}});
    listen('did-fail-load',(_e,code,description,failedUrl,isMain)=>{
      if(!isMain)return;
      if(code===-3)return; // Redirects and newer navigation can abort a provisional load.
      finish(Error(description+' ('+code+')：'+failedUrl));
    });
    listen('render-process-gone',(_e,details)=>finish(Error('网页进程已退出：'+details.reason)));
    listen('destroyed',()=>finish(Error('网页窗口已关闭')));
    publish(state);
    timer=setTimeout(()=>{
      finish(Error('网页连接超时，请修改地址或检查网络后重试'));
      if(!page.isDestroyed())page.stop();
    },Math.max(1000,timeoutMs));
    try{
      page.loadURL(url).then(()=>finish(),error=>{
        if(!finished)finish(error);
      });
    }catch(error){finish(error);}
  });
};
