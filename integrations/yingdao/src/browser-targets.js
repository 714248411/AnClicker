// Enumerate every live, managed browser page without changing the active engine.
async function listTargets(windows, external, session) {
  const pages = [];
  for (const b of windows) {
    try {
      if (b.win.isDestroyed() || b.win.webContents.isDestroyed()) continue;
      pages.push({id:b.id,cdpKey:b.cdpKey || null,url:b.win.webContents.getURL(),title:b.win.webContents.getTitle(),badge:b.badge || '',mode:b.mode || '',slot:b.slot || null,engine:'内置',session});
    } catch (_) { /* A window can close during enumeration. */ }
  }
  let warning = '';
  if (external.isRunning()) {
    try {
      const kind = external.info().kind || '内置Chrome';
      for (const p of await external.listPages()) pages.push({...p,badge:kind,mode:kind,slot:null,engine:kind,session});
    } catch (error) { warning = '外部浏览器刷新失败：'+error.message; }
  }
  return {pages,warning};
}
module.exports = {listTargets};
