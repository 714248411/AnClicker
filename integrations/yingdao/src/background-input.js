// CDP-only input. Never focus, restore or activate an OS window.
async function click(send, {x, y, clickType = '单击'}) {
  x = Number(x); y = Number(y);
  if (!Number.isFinite(x) || !Number.isFinite(y) || x < 0 || y < 0) throw new Error('网页坐标必须为非负数字');
  const metrics = await send('Page.getLayoutMetrics', {});
  const viewport = metrics.cssVisualViewport || metrics.visualViewport;
  if (viewport && (x >= viewport.clientWidth || y >= viewport.clientHeight)) throw new Error('坐标超出网页可视区域，请重新取点');
  const button = clickType === '右键' ? 'right' : 'left';
  const buttons = button === 'right' ? 2 : 1;
  await send('Input.dispatchMouseEvent', {type:'mouseMoved', x, y, button:'none', buttons:0});
  for (let count = 1; count <= (clickType === '双击' ? 2 : 1); count++) {
    try { await send('Input.dispatchMouseEvent', {type:'mousePressed', x, y, button, buttons, clickCount:count}); }
    finally { await send('Input.dispatchMouseEvent', {type:'mouseReleased', x, y, button, buttons:0, clickCount:count}); }
  }
  return {x, y};
}
async function key(send, spec) {
  if (!spec || !spec.key) throw new Error('请填写按键');
  const modifiers = (spec.modifiers || []).reduce((bits, name) => bits | ({alt:1,control:2,meta:4,shift:8}[name] || 0), 0);
  let value = spec.key;
  const aliases = {Esc:'Escape',Space:' ',Up:'ArrowUp',Down:'ArrowDown',Left:'ArrowLeft',Right:'ArrowRight'};
  value = aliases[value] || value;
  const known = {Insert:45,Shift:16,Control:17,Alt:18,Meta:91,Enter:13,Tab:9,Escape:27,Backspace:8,Delete:46,ArrowUp:38,ArrowDown:40,ArrowLeft:37,ArrowRight:39,Home:36,End:35,PageUp:33,PageDown:34,' ':32};
  const vk = known[value] || (/^F([1-9]|1[0-2])$/.test(value) ? 111 + Number(value.slice(1)) : value.length === 1 ? value.toUpperCase().charCodeAt(0) : spec.keyCode || 0);
  const code = value === ' ' ? 'Space' : /^[a-z]$/i.test(value) ? 'Key'+value.toUpperCase() : /^[0-9]$/.test(value) ? 'Digit'+value : value;
  const base = {key:value, code, windowsVirtualKeyCode:vk, nativeVirtualKeyCode:vk, modifiers};
  // Setting page focus through CDP preserves the OS foreground window.
  await send('Emulation.setFocusEmulationEnabled', {enabled:true});
  try {
    try {
      await send('Input.dispatchKeyEvent', {...base,type:'rawKeyDown'});
      const text = value === 'Enter' ? '\r' : Array.from(value).length === 1 ? ((modifiers & 8) ? value.toUpperCase() : value) : '';
      if (!(modifiers & 7) && text) await send('Input.dispatchKeyEvent', {...base,type:'char',text,unmodifiedText:text});
    } finally { await send('Input.dispatchKeyEvent', {...base,type:'keyUp'}); }
  } finally { await send('Emulation.setFocusEmulationEnabled', {enabled:false}); }
  return value;
}
module.exports = {click, key};
