'use strict';
const api=window.browserControls;
const trigger=document.getElementById('trigger'),panel=document.getElementById('panel'),address=document.getElementById('address'),status=document.getElementById('status');
let state={},expanded=false,editing=false,submission=0;
async function call(action,value){const response=await api.call(action,value);if(!response.ok)throw Error(response.error);return response.result;}
function updateToggle(){
  const label=expanded?'隐藏网页工具栏':'展开网页工具栏';
  trigger.title=label+(status.className==='error'?'：'+status.textContent:'');
  trigger.setAttribute('aria-label',label);trigger.setAttribute('aria-expanded',String(expanded));
}
function expand(value){expanded=value;panel.hidden=!value;updateToggle();call('expand',value).catch(showError);}
function showError(error){status.textContent='打开失败：'+String(error.message||error);status.title=status.textContent;status.className='error';trigger.classList.add('error');updateToggle();}
function render(next){
  state=next;
  if(!editing)address.value=(state.error||state.loading)?(state.requestedUrl||state.url||''):(state.url||state.requestedUrl||'');
  status.className=state.error?'error':'';
  status.textContent=state.error?'打开失败：'+state.error:state.loading?'正在加载…':'';
  document.getElementById('zoom').textContent=state.zoom+'%';
  document.getElementById('back').disabled=!state.canBack;document.getElementById('forward').disabled=!state.canForward;
  status.title=status.textContent;trigger.classList.toggle('error',!!state.error);updateToggle();
}
trigger.addEventListener('click',()=>{if(expanded)address.blur();expand(!expanded);});
address.addEventListener('focus',()=>{editing=true;});
address.addEventListener('blur',()=>{editing=false;});
document.getElementById('addressForm').addEventListener('submit',async event=>{
  event.preventDefault();const id=++submission;const value=address.value.trim();
  if(!value){showError('请填写网页地址');return;}
  editing=false;address.blur();state={...state,requestedUrl:value,loading:true,error:''};status.className='';status.textContent='正在打开…';
  try{await call('open',value);}catch(error){if(id===submission)showError(error);}
});
for(const button of document.querySelectorAll('[data-action]'))button.onclick=()=>call(button.dataset.action,button.dataset.value).catch(showError);
api.onState(render);call('state').then(render).catch(showError);
