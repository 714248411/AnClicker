'use strict';
let busy = false;
window.acHost.onRequest(async msg => {
  if (busy) { window.acHost.respond({id:msg.id,error:'执行引擎忙，请等待当前指令完成'}); return; }
  busy = true;
  const logs = [];
  try {
    Engine.resetCancel();
    Engine.vars = msg.variables || {};
    let result;
    if (msg.operation === 'inspect') {
      result = {books:Engine.getBooks(), tabs:await window.yingdao.browser.getTabs(), titles:await window.acHost.windowTitles()};
    } else {
      const cmd = msg.command;
      if (!cmd || typeof cmd.id !== 'string') throw new Error('缺少指令');
      if (cmd.id === 'acRecordStart' || cmd.id === 'acRecordStop' || cmd.id === 'acRecordStatus') {
        result = await window.acHost.recordControl({acRecordStart:'start',acRecordStop:'stop',acRecordStatus:'status'}[cmd.id]);
      } else if (cmd.id === 'acAgent') {
        result = await window.acHost.agent(cmd.params);
      } else if (cmd.id === 'acInspect') {
        result = {tabs:await window.yingdao.browser.getTabs(), titles:await window.acHost.windowTitles()};
      } else if (cmd.id === 'screenshot') {
        if (!cmd.params.path) throw new Error('请填写截图保存路径');
        result = await window.acHost.screenshot(Engine.expand(cmd.params.selector),Engine.expand(cmd.params.path));
      } else {
        result = await Engine.runCommand(cmd, {log:s=>logs.push(String(s))});
      }
    }
    window.acHost.respond({id:msg.id,result:result===undefined?null:result,variables:Engine.vars,logs});
  } catch (e) { window.acHost.respond({id:msg.id,error:String(e.message || e),logs}); }
  finally { busy = false; }
});
window.acHost.ready();
