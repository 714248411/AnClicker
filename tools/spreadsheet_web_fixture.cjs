const fs=require('fs'),path=require('path'),XLSX=require('../integrations/yingdao/src/lib/xlsx.full.min.js');
const out=path.resolve('artifacts/debug/spreadsheet-web');
if(process.argv[2]==='seed'){
 const book=XLSX.utils.book_new();XLSX.utils.book_append_sheet(book,XLSX.utils.aoa_to_sheet([['WRONG SHEET']]),'不要读取');
 XLSX.utils.book_append_sheet(book,XLSX.utils.aoa_to_sheet([['00123',"中文 O'Brien"],[0,'${secret}']]),'数据');
 fs.writeFileSync(path.join(out,'source.xlsx'),XLSX.write(book,{bookType:'xlsx',type:'buffer'}));
 const dst=XLSX.utils.book_new();XLSX.utils.book_append_sheet(dst,XLSX.utils.aoa_to_sheet([['保留原内容']]),'结果');
 fs.writeFileSync(path.join(out,'result.xlsx'),XLSX.write(dst,{bookType:'xlsx',type:'buffer'}));console.log('FIXTURES_READY');
}else{
 const dst=XLSX.read(fs.readFileSync(path.join(out,'result.xlsx')),{type:'buffer'});
 const ws=dst.Sheets['结果'];const expected="00123\t中文 O'Brien\n0\t"+'${secret}';
 if(ws.C3.v!==expected||ws.C3.t!=='s'||ws.A1.v!=='保留原内容')throw Error(JSON.stringify(ws));
 if(ws.E1.v!=='00123'||ws.E2.v!=='=2+2'||ws.E2.f||ws.E3.v!=='中文')throw Error('Literal text or leading zeros corrupted');
 console.log(JSON.stringify({passed:true,C3:ws.C3,E1:ws.E1,E2:ws.E2,E3:ws.E3}));
}