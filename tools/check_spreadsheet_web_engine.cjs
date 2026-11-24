const assert=require('assert'),vm=require('vm'),fs=require('fs');
const XLSX=require('../integrations/yingdao/src/lib/xlsx.full.min.js');
const context={window:{yingdao:{readFile:async p=>fs.readFileSync(p)}},XLSX,console,setTimeout};vm.createContext(context);
vm.runInContext(fs.readFileSync('integrations/yingdao/src/engine.js','utf8'),context);
vm.runInContext(fs.readFileSync('integrations/yingdao/src/commands.js','utf8'),context);
const json=JSON.parse(fs.readFileSync('integrations/yingdao/commands.json','utf8'));
for(const id of ['excelOpen','excelReadRange','input']){
 const a=context.window.COMMANDS.find(x=>x.id===id),b=json.find(x=>x.id===id);
 assert.deepStrictEqual(JSON.parse(JSON.stringify(a.params)).sort((x,y)=>x.key.localeCompare(y.key)),b.params.sort((x,y)=>x.key.localeCompare(y.key)));
}
(async()=>{
 const engine=context.window.Engine;
 await engine.excelOpen('artifacts/debug/spreadsheet-web/source.xlsx');
 assert.strictEqual(engine.excelRead('A1'),'WRONG SHEET');
 await engine.excelOpen('artifacts/debug/spreadsheet-web/source.xlsx','数据');
 assert.strictEqual(engine.excelReadRange('A1:B2')[1][0],0);
 assert.strictEqual(engine.excelReadRange('A1:B2','制表符文本'),"00123\t中文 O'Brien\n0\t"+'${secret}');
 engine.getWS().C1={t:'n',v:42,z:'00000'};
 assert.strictEqual(engine.excelReadRange('C1:C1','制表符文本'),'00042');
 assert.strictEqual(engine.excelReadRange('C1:C1')[0][0],42);
 await assert.rejects(()=>engine.excelOpen('artifacts/debug/spreadsheet-web/source.xlsx','Missing'),/工作表/);
 await assert.rejects(()=>engine.input({selector:'#x',textVariable:'missing'}),/未找到输入变量/);
 console.log('PASS legacy matrix format, sheet selection, TSV values, missing-variable rejection and catalog consistency');
})().catch(e=>{console.error(e);process.exitCode=1;});
