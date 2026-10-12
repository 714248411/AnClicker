'use strict';
// Runtime configuration only. Never persist proxy endpoints or credentials.
function proxyConfig(env) {
  const raw=env.HTTPS_PROXY || env.https_proxy || env.ALL_PROXY || env.all_proxy || env.HTTP_PROXY || env.http_proxy;
  if(!raw)return null;
  try {
    const url=new URL(raw);
    if(url.username || url.password)return null; // Authentication remains managed by system settings.
    const scheme=url.protocol==='socks5h:'?'socks5:':url.protocol;
    if(!['http:','https:','socks5:','socks4:'].includes(scheme))return null;
    return {proxyRules:scheme+'//'+url.host,proxyBypassRules:String(env.NO_PROXY || env.no_proxy || '').split(',').map(s=>s.trim()).filter(Boolean).join(';')};
  } catch (_) {return null;}
}
const configured=new WeakMap();
async function configureSession(session, env=process.env) {
  const config=proxyConfig(env);
  if(!config)return;
  if(!configured.has(session))configured.set(session,session.setProxy(config).catch(error=>{configured.delete(session);throw error;}));
  await configured.get(session);
}
module.exports={proxyConfig,configureSession};
