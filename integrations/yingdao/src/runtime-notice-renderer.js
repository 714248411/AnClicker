'use strict';
const api=window.runtimeNotice;
api.onState(state=>{document.getElementById('message').textContent=state.message||'';document.getElementById('reconnect').disabled=!!state.reconnecting;document.getElementById('reconnect').textContent=state.reconnecting?'正在重连…':'自动重连';});
for(const action of ['copy','reconnect','dismiss'])document.getElementById(action).onclick=()=>api.call(action).catch(()=>{});
api.call('state').catch(()=>{});
