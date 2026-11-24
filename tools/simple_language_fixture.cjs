const fs=require('fs'),X=require('../integrations/yingdao/src/lib/xlsx.full.min.js');
const b=X.utils.book_new();X.utils.book_append_sheet(b,X.utils.aoa_to_sheet([['姓名','编号','备注'],['张三','00123','${secret}'],['李四','00007',"O'Brien😀"]]),'数据');fs.writeFileSync('artifacts/debug/simple-language/source.xlsx',X.write(b,{type:'buffer',bookType:'xlsx'}));
