const assert=require('assert');
const {EventEmitter}=require('events');
const {recover,cancel}=require('../integrations/yingdao/src/browser-recovery');
(async()=>{
 const page=new EventEmitter();page.isDestroyed=()=>false;let calls=0,reports=[];
 assert.equal(await recover(page,'url',async()=>{if(++calls<3)throw Error('ECONNRESET');return 'ready';},(...args)=>reports.push(args)),'ready');
 assert.equal(calls,3);assert.equal(reports.length,2);
 calls=0;await assert.rejects(recover(page,'url',async()=>{calls++;throw Error('invalid selector');},()=>{}),/invalid selector/);assert.equal(calls,1);
 calls=0;const waiting=recover(page,'old',async()=>{calls++;throw Error('ERR_CONNECTION_RESET');},()=>{});setTimeout(()=>cancel(page),20);await assert.rejects(waiting,e=>e.code==='NAVIGATION_REPLACED');assert.equal(calls,1);
 assert.equal(page.listenerCount('destroyed'),0);
 require('fs').writeFileSync(require('path').join(__dirname,'../artifacts/validation/check_browser_recovery.cjs.passed'),'PASS');console.log('PASS transient retries, non-network failure, cancellation and listener cleanup');
})().catch(e=>{console.error(e);process.exitCode=1;});
