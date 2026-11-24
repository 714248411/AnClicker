/* Shared locator for execution and visual preview. No page state is cached. */
(function (root) {
  'use strict';
  function resolve(options) {
    'use strict';
    options = options || {};
    const normalize = value => String(value == null ? '' : value).replace(/\s+/g, ' ').trim();
    const unique = list => Array.from(new Set(list));
    const splitLegacy = value => {
      const parts = []; let token = '', quote = '', depth = 0, escaped = false;
      for (const ch of String(value || '')) {
        if (escaped) { token += ch; escaped = false; continue; }
        if (ch === '\\') { token += ch; escaped = true; continue; }
        if (quote) { token += ch; if (ch === quote) quote = ''; continue; }
        if (ch === '"' || ch === "'") { quote = ch; token += ch; continue; }
        if (ch === '[' || ch === '(') depth++;
        if (ch === ']' || ch === ')') depth--;
        if (!depth && (ch === ';' || ch === '；' || ch === '\n')) { if (token.trim()) parts.push(token.trim()); token = ''; }
        else token += ch;
      }
      if (token.trim()) parts.push(token.trim());
      return parts;
    };
    let config = {}, rules;
    const raw = String(options.anchor || '').trim();
    try {
      if (raw[0] === '{' || /^\[\s*(?:\{|"|\])/.test(raw)) {
        const parsed = JSON.parse(raw);
        config = Array.isArray(parsed) ? {anchors:parsed} : parsed;
        rules = config.anchors;
        if (!Array.isArray(rules)) throw Error('缺少 anchors 列表');
      } else rules = splitLegacy(raw).map(selector => ({selector}));
    } catch (error) {
      return {element:null, report:{found:false, count:0, reason:'锚点配置格式错误：'+error.message, anchors:[]}};
    }
    if (!rules.length || rules.length > 20) return {element:null,report:{found:false,count:0,reason:'请设置 1 至 20 个锚点',anchors:[]}};
    const relationNames = ['下方','上方','右侧','左侧','内部','相邻','同一行','同一列','最近'];
    rules = rules.map(rule => typeof rule === 'string' ? {selector:rule} : (rule || {})).map(rule => ({
      selector:String(rule.selector || '').trim(), by:rule.by || '智能匹配', relation:rule.relation || options.relation || '下方'
    }));
    if (rules.some(rule => !rule.selector || !['智能匹配','CSS选择器','XPath','文本内容'].includes(rule.by) || !relationNames.includes(rule.relation))) return {element:null,report:{found:false,count:0,reason:'锚点内容或相对方位无效',anchors:[]}};
    const maxDistance = config.maxDistance == null ? 800 : Number(config.maxDistance);
    const matchIndex = Number(config.matchIndex || 0);
    if (!Number.isFinite(maxDistance) || maxDistance < 0 || maxDistance > 100000 || !Number.isInteger(matchIndex) || matchIndex < 0 || matchIndex > 10000) return {element:null,report:{found:false,count:0,reason:'最大距离和匹配序号必须为非负数',anchors:[]}};
    const roots = [], seenRoots = new Set();
    function walk(root, depth) {
      if (!root || seenRoots.has(root) || roots.length >= 80 || depth > 12) return;
      seenRoots.add(root); roots.push(root);
      for (const el of Array.from(root.querySelectorAll('*')).slice(0,20000)) {
        if (el.shadowRoot) walk(el.shadowRoot, depth+1);
        if (el.tagName === 'IFRAME' || el.tagName === 'FRAME') {
          try { if (el.contentDocument) walk(el.contentDocument, depth+1); } catch (_) {}
        }
      }
    }
    walk(document,0);
    function visible(el) {
      if (!el || el.nodeType !== 1 || !el.isConnected || el.closest('[data-anclicker-locator-preview]')) return false;
      const rect = el.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0 || el.closest('[hidden],[aria-hidden="true"]')) return false;
      let current = el;
      while (current && current.nodeType === 1) {
        const style = current.ownerDocument.defaultView.getComputedStyle(current);
        if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) return false;
        current = current.parentElement || (current.getRootNode && current.getRootNode().host);
      }
      try { const frame=el.ownerDocument.defaultView.frameElement; if(frame && !visible(frame)) return false; } catch (_) {}
      return true;
    }
    function text(el) {
      return normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || el.getAttribute('title') || el.getAttribute('placeholder') || el.value || el.alt);
    }
    function query(value, by) {
      let source = String(value || '').trim();
      const prefix = source.match(/^(css|xpath|text)\s*[:=]\s*([\s\S]*)$/i);
      if (prefix) { by = {css:'CSS选择器',xpath:'XPath',text:'文本内容'}[prefix[1].toLowerCase()]; source = prefix[2]; }
      const all = [], css = [], xp = [];
      for (const root of roots) {
        try { css.push(...root.querySelectorAll(source)); } catch (_) {}
        if (by === 'XPath' || (by === '智能匹配' && /^[(/]/.test(source))) {
          try {
            const doc = root.ownerDocument || root;
            const result = doc.evaluate(source,root,null,7,null);
            for (let i=0;i<result.snapshotLength;i++) xp.push(result.snapshotItem(i));
          } catch (_) {}
        }
      }
      if (by === 'CSS选择器') return unique(css).filter(visible);
      if (by === 'XPath') return unique(xp).filter(visible);
      if (by === '智能匹配' && css.some(visible)) return unique(css).filter(visible);
      if (by === '智能匹配' && xp.some(visible)) return unique(xp).filter(visible);
      const wanted = normalize(source);
      if (!wanted) return [];
      for (const root of roots) {
        for (const el of Array.from(root.querySelectorAll('*')).slice(0,20000)) {
          if (/^(HTML|BODY|HEAD|SCRIPT|STYLE|NOSCRIPT|META|LINK)$/.test(el.tagName) || !visible(el)) continue;
          all.push(el);
        }
      }
      const exact = all.filter(el => text(el) === wanted);
      // Prefer leaf matches: a large wrapper with the same text is not an anchor.
      const leaf = list => list.filter(el => !Array.from(el.children).some(child => list.includes(child)));
      if (exact.length) return unique(leaf(exact));
      if (by === '文本内容') return [];
      const contains = all.filter(el => text(el).includes(wanted));
      if (contains.length) return unique(leaf(contains));
      return unique(all.filter(el => ['id','name','aria-label','placeholder','title','alt'].some(attr => normalize(el.getAttribute(attr)) === wanted)));
    }
    function contains(parent,child) {
      let current=child;
      while (current) {
        if (current===parent) return true;
        current=current.parentElement || (current.getRootNode && current.getRootNode().host);
      }
      return false;
    }
    function metric(target, anchor, relation) {
      if (target===anchor || target.ownerDocument!==anchor.ownerDocument || contains(target,anchor)) return null;
      const t=target.getBoundingClientRect(), a=anchor.getBoundingClientRect();
      const dx=(t.left+t.right-a.left-a.right)/2, dy=(t.top+t.bottom-a.top-a.bottom)/2;
      const overlapX=Math.min(t.right,a.right)-Math.max(t.left,a.left);
      const overlapY=Math.min(t.bottom,a.bottom)-Math.max(t.top,a.top);
      const gapX=Math.max(0,t.left-a.right,a.left-t.right), gapY=Math.max(0,t.top-a.bottom,a.top-t.bottom);
      let valid=false;
      if (relation==='内部') valid=contains(anchor,target);
      else if (relation==='相邻') valid=anchor.nextElementSibling && contains(anchor.nextElementSibling,target);
      else if (contains(anchor,target)) return null;
      else if (relation==='下方') valid=t.top>=a.bottom-6 && overlapX>0;
      else if (relation==='上方') valid=t.bottom<=a.top+6 && overlapX>0;
      else if (relation==='右侧') valid=t.left>=a.right-6 && overlapY>0;
      else if (relation==='左侧') valid=t.right<=a.left+6 && overlapY>0;
      else if (relation==='同一行') valid=overlapY>0 && Math.abs(dy)<=Math.max(6,Math.min(t.height,a.height)/2);
      else if (relation==='同一列') valid=overlapX>0 && Math.abs(dx)<=Math.max(6,Math.min(t.width,a.width)/2);
      else if (relation==='最近') valid=true;
      if (!valid) return null;
      const distance=Math.hypot(gapX,gapY);
      if (maxDistance && distance>maxDistance) return null;
      return distance+Math.hypot(dx,dy)*.05;
    }
    const anchorMatches=rules.map(rule => query(rule.selector,rule.by));
    const anchorReport=rules.map((rule,i)=>({selector:rule.selector,by:rule.by,relation:rule.relation,count:anchorMatches[i].length}));
    const missing=anchorMatches.findIndex(matches=>!matches.length);
    if (missing>=0) return {element:null,report:{found:false,count:0,anchors:anchorReport,reason:'第 '+(missing+1)+' 个锚点未找到或不可见'}};
    const targetQuery=String(options.selector || '').trim();
    const targetBy=config.targetBy || '智能匹配';
    const candidates=targetQuery ? query(targetQuery,targetBy) : query('input,textarea,select,button,a,[role="button"],[contenteditable="true"]','CSS选择器');
    const ranked=[];
    for (const candidate of candidates) {
      if (config.frameUrl && candidate.ownerDocument.URL!==config.frameUrl) continue;
      if (config.frameName && candidate.ownerDocument.defaultView.name!==config.frameName) continue;
      let score=0;const chosen=[];
      for (let i=0;i<rules.length;i++) {
        const valid=anchorMatches[i].map(anchor=>({anchor,score:metric(candidate,anchor,rules[i].relation)})).filter(item=>item.score!==null).sort((a,b)=>a.score-b.score);
        if (!valid.length) { score=null;break; }
        score+=valid[0].score;chosen.push(valid[0].anchor);
      }
      if (score!==null) ranked.push({element:candidate,score,anchors:chosen});
    }
    ranked.sort((a,b)=>a.score-b.score);
    let chosen=null,reason='没有目标同时满足全部锚点、方位与距离条件；请检查目标与锚点是否在同一网页框架中';
    if (matchIndex>0) {
      // An explicit index follows visual reading order, independent of DOM order.
      ranked.sort((a,b)=>{const x=a.element.getBoundingClientRect(),y=b.element.getBoundingClientRect();return x.top-y.top || x.left-y.left;});
      chosen=ranked[matchIndex-1] || null;
      reason=chosen?'已按匹配序号定位':'匹配序号超过当前候选数量';
    } else if (ranked.length===1 || (ranked.length>1 && ranked[1].score-ranked[0].score>2)) {
      chosen=ranked[0];reason='全部锚点联合匹配成功';
    } else if (ranked.length>1) reason='多个目标同样符合锚点，无法唯一定位；请增加锚点、缩小目标条件或指定匹配序号';
    function describe(el) {const r=el.getBoundingClientRect();return {tag:el.tagName,text:text(el).slice(0,100),rect:{x:r.x,y:r.y,width:r.width,height:r.height}};}
    const report={found:!!chosen,count:ranked.length,anchors:anchorReport,reason,target:chosen?describe(chosen.element):null,candidates:ranked.slice(0,10).map(item=>describe(item.element))};
    if (options.highlight && chosen) {
      chosen.element.scrollIntoView({block:'center',inline:'center'});
      const doc=chosen.element.ownerDocument;
      const draw=(el,color,label)=>{
        const r=el.getBoundingClientRect(),box=doc.createElement('div');
        box.setAttribute('data-anclicker-locator-preview','true');
        box.style.cssText='position:fixed;pointer-events:none;z-index:2147483646;box-sizing:border-box;border:3px solid '+color+';left:'+r.left+'px;top:'+r.top+'px;width:'+r.width+'px;height:'+r.height+'px;';
        box.title=label;(doc.body || doc.documentElement).appendChild(box);setTimeout(()=>box.remove(),3500);
      };
      doc.querySelectorAll('[data-anclicker-locator-preview]').forEach(el=>el.remove());
      chosen.anchors.forEach(el=>draw(el,'#f59e0b','锚点'));draw(chosen.element,'#16a34a','目标');
    }
    return {element:chosen?chosen.element:null, report};
  }
  const api={resolve};
  if (typeof module==='object' && module.exports) module.exports=api;
  if (root) root.AnClickerAnchorLocator=api;
})(typeof window!=='undefined'?window:null);
