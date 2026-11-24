/* Geometry in CSS pixels, bounded to the same table limits as extraction. */
function tableLayout(table) {
  const rect=table.getBoundingClientRect(), rows=Array.from(table.rows).filter(r=>r.closest('table')===table).slice(0,100);
  if(!rect.width||!rect.height)return null;
  const cells=[],used=new Set(),bounds=[];
  const px=v=>Math.max(0,parseFloat(v)||0);
  rows.forEach((row,r)=>{
    let c=0;
    Array.from(row.cells).slice(0,50).forEach(cell=>{
      while(used.has(r+','+c))c++;
      if(c>=50)return;
      const rs=Math.min(cell.rowSpan||rows.length-r,rows.length-r),cs=Math.min(cell.colSpan||1,50-c);
      for(let i=r;i<r+rs;i++)for(let j=c;j<c+cs;j++)used.add(i+','+j);
      const b=cell.getBoundingClientRect(),s=getComputedStyle(cell);
      bounds[c]=b.left-rect.left;bounds[c+cs]=b.right-rect.left;
      cells.push({row:r,col:c,rowspan:rs,colspan:cs,fontSize:px(s.fontSize),fontFamily:s.fontFamily.split(',')[0].replace(/["']/g,''),bold:parseInt(s.fontWeight)>=600,
        lineHeight:px(s.lineHeight)||px(s.fontSize)*1.2,align:s.textAlign,vertical:s.verticalAlign,
        padding:['Top','Right','Bottom','Left'].map(k=>px(s['padding'+k])),
        x:b.left-rect.left,y:b.top-rect.top,w:b.width,h:b.height});c+=cs;
    });
  });
  // Use known span edges; interpolate only columns that have no unmerged cell.
  bounds[0]=bounds[0]||0;
  for(let i=1;i<bounds.length;i++)if(bounds[i]===undefined){let end=i+1;while(bounds[end]===undefined)end++;bounds[i]=bounds[i-1]+(bounds[end]-bounds[i-1])/(end-i+1);}
  return {width:rect.width,height:rect.height,top:rect.top+scrollY,
    columns:bounds.slice(1).map((x,i)=>Math.max(1,x-bounds[i])),
    heights:rows.map(row=>row.getBoundingClientRect().height),cells};
}
if(typeof module!=='undefined')module.exports=tableLayout;
