import {jobs,reports,products} from '../api/entities.js';
import {download} from '../api/client.js';
import {workspace} from '../stores/workspace.js';
import {session} from '../stores/session.js';
import {heading} from '../components/common/shell.js';
import {esc,date,notify} from '../utils/dom.js';
import {submit} from '../hooks/forms.js';
export async function reportPage(){
 const [list,deliveries,allJobs,productList]=await Promise.all([reports.list(),reports.deliveries(),jobs.list(),products.list()]);workspace.reports=list;
 const approved=allJobs.filter(j=>j.approved&&j.status==='completed');
 const versions={};await Promise.all(productList.map(async p=>{versions[p.id]=await products.versions(p.id);}));
 const admin=session.user.role==='admin';
 const jobName=id=>{const j=allJobs.find(x=>x.id===id);return j?j.name:'#'+id;};
 const productName=id=>{const p=productList.find(x=>x.id===id);return p?p.name:'#'+id;};
 const productSection='<section class="panel"><div class="section-title"><h2>产品结论版本</h2><span>'+productList.length+' 个产品 · 负责人发布或回退，订阅计划每期采用届时现行版本</span></div>'
  +productList.map(p=>{
   const cur=p.current_version,hist=versions[p.id]||[];
   return '<article class="product"><div class="product-head"><div><strong>'+esc(p.name)+'</strong><p>'+(cur?'现行 第'+cur.version+'版 · 分析「'+esc(cur.job_name)+'」 · '+(cur.kind==='rollback'?'回退发布':'发布')+'于 '+date(cur.created_at):'尚未发布结论 · 订阅计划暂不出刊')+'</p></div>'
   +(admin?'<div class="product-actions"><details><summary class="button small">发布新版本</summary><form class="publish-form" data-product="'+p.id+'"><input type="hidden" name="expected_version" value="'+(cur?cur.version:0)+'"><input type="hidden" name="request_id" value="'+crypto.randomUUID()+'"><label>已批准分析<select name="job_id" required>'+approved.map(j=>'<option value="'+j.id+'">'+esc(j.name)+'</option>').join('')+'</select></label><button type="submit" class="primary small" '+(approved.length?'':'disabled')+'>基于第'+(cur?cur.version:0)+'版发布</button></form></details><details><summary class="button small">回退到历史版本</summary><form class="rollback-form" data-product="'+p.id+'"><input type="hidden" name="expected_version" value="'+(cur?cur.version:0)+'"><input type="hidden" name="request_id" value="'+crypto.randomUUID()+'"><label>历史版本<select name="target_version_id" required>'+hist.filter(v=>!cur||v.id!==cur.id).map(v=>'<option value="'+v.id+'">第'+v.version+'版 · '+esc(v.job_name)+' · '+date(v.created_at)+'</option>').join('')+'</select></label><button type="submit" class="button small" '+(hist.some(v=>!cur||v.id!==cur.id)?'':'disabled')+'>回退并生成新版本</button></form></details></div>':'')
   +'</div><ol class="version-trail">'+hist.map(v=>'<li'+(cur&&v.id===cur.id?' class="current"':'')+'>第'+v.version+'版 · '+esc(v.job_name)+' · '+(v.kind==='rollback'?'回退自第'+((hist.find(x=>x.id===v.source_version_id)||{}).version||'?')+'版':'发布')+' · '+esc(v.created_by)+' · '+date(v.created_at)+(cur&&v.id===cur.id?' · 现行':'')+'</li>').join('')+'</ol></article>';
  }).join('')
  +(admin?'<form id="product-form" class="inline-form"><input name="name" required minlength="2" maxlength="160" placeholder="新产品名称，如：反应釜运行窗口 · 工艺结论"><button type="submit" class="button small">新建产品</button></form>':'')
  +(!productList.length?'<p class="empty">还没有产品。负责人新建产品后，可从已批准分析发布第 1 版结论。</p>':'')+'</section>';
 const createForm='<section class="panel"><div class="section-title"><h2>创建分发计划</h2></div><form id="report-form"><label>简报名称<input name="name" required minlength="2" value="日间业务复核简报"></label><label>内容来源<select name="source" id="report-source"><option value="product">订阅产品结论 · 跟随现行版本</option><option value="job">固定分析快照 · 传统方式</option></select></label><label data-source="product">订阅产品<select name="product_id">'+productList.map(p=>'<option value="'+p.id+'">'+esc(p.name)+'</option>').join('')+'</select></label><label data-source="job" hidden>已批准分析<select name="job_id">'+approved.map(j=>'<option value="'+j.id+'">'+esc(j.name)+'</option>').join('')+'</select></label><label>业务接收组<input name="destination" value="业务复核组 · 本地收件箱" required></label><div class="parameter-grid"><label>分发周期<select name="interval_seconds"><option value="86400">每日</option><option value="604800">每周</option><option value="60">每分钟（验收）</option></select></label><label>首次执行<select name="delay_seconds"><option value="0">立即</option><option value="60">1 分钟后</option><option value="3600">1 小时后</option></select></label></div><button type="submit" class="primary" '+(admin&&(approved.length||productList.length)?'':'disabled')+'>保存分发计划</button></form><p class="hint">订阅产品的计划每期开始固定届时现行版本与接收组，发布或回退不改变在途期次；产品未发布结论则不出刊。固定分析计划保持原快照行为。</p></section>';
 const scheduleList='<section><div class="section-title"><h2>运行中的计划</h2><span>'+list.filter(r=>r.enabled).length+' 条已启用</span></div><div class="schedule-list">'+list.map(r=>'<article><div><strong>'+esc(r.name)+'</strong><p>'+esc(r.destination)+'</p><small>'+(r.product_id?'订阅产品 · '+esc(productName(r.product_id)):'固定分析 · '+esc(jobName(r.job_id)))+' · 下次 '+date(r.next_run)+' · 周期 '+r.interval_seconds+' 秒</small></div><button class="button small" data-toggle="'+r.id+'" '+(admin?'':'disabled')+'>'+(r.enabled?'暂停':'启用')+'</button></article>').join('')+'</div>';
 const inbox='<section class="panel inbox"><div class="section-title"><h2>本地收件箱</h2><span>'+deliveries.length+' 份归档</span></div>'+deliveries.map(d=>'<div class="delivery"><div><strong>'+esc(d.filename)+'</strong><p>'+esc(d.destination)+' · '+date(d.created_at)+'</p><small>'+(d.version?'采用 '+esc(d.product)+' · 第'+d.version+'版结论':'固定分析快照')+' · SHA256 '+esc(d.checksum.slice(0,24))+'…</small></div><div><button class="text-button" data-download="'+d.id+'" data-format="csv">CSV ↓</button><button class="text-button" data-download="'+d.id+'" data-format="json">JSON ↓</button></div></div>').join('')+(!deliveries.length?'<p class="empty">计划执行后，文件会出现在此处。等待片刻后刷新。</p>':'')+'</section></section>';
 return heading('05 / DISTRIBUTION','定时分发与归档','按产品维护现行工艺结论：负责人发布或回退版本，订阅计划每期固定届时版本交付到本地业务收件箱。','<button class="button" id="refresh-reports">刷新收件箱 ↻</button>')+productSection+'<div class="report-grid">'+createForm+scheduleList+inbox+'</div>';
}
export function bindReports(refresh){
 document.querySelector('#refresh-reports').onclick=refresh;
 const source=document.querySelector('#report-source');
 const toggleSource=()=>document.querySelectorAll('[data-source]').forEach(el=>{el.hidden=el.dataset.source!==source.value;});
 if(source){source.onchange=toggleSource;toggleSource();}
 submit(document.querySelector('#report-form'),async f=>{
  const payload={name:f.get('name'),destination:f.get('destination'),interval_seconds:Number(f.get('interval_seconds')),delay_seconds:Number(f.get('delay_seconds'))};
  if(f.get('source')==='product')payload.product_id=Number(f.get('product_id'));else payload.job_id=Number(f.get('job_id'));
  await reports.create(payload);notify('计划已保存，后台将按到期时间归档');await refresh();
 });
 const productForm=document.querySelector('#product-form');
 if(productForm)submit(productForm,async f=>{await products.create({name:f.get('name')});notify('产品已创建，可发布第 1 版结论');await refresh();});
 document.querySelectorAll('.publish-form').forEach(form=>submit(form,async f=>{
  await products.publish(form.dataset.product,{job_id:Number(f.get('job_id')),expected_version:Number(f.get('expected_version')),request_id:f.get('request_id')});
  notify('新版本已发布，下一期订阅简报将采用');await refresh();
 }));
 document.querySelectorAll('.rollback-form').forEach(form=>submit(form,async f=>{
  await products.rollback(form.dataset.product,{target_version_id:Number(f.get('target_version_id')),expected_version:Number(f.get('expected_version')),request_id:f.get('request_id')});
  notify('已回退并生成新版本，历史链完整保留');await refresh();
 }));
 document.querySelectorAll('[data-toggle]').forEach(b=>b.onclick=async()=>{try{await reports.toggle(b.dataset.toggle);await refresh();}catch(e){notify(e.message,true);}});
 document.querySelectorAll('[data-download]').forEach(b=>b.onclick=()=>download(b.dataset.download,b.dataset.format).catch(e=>notify(e.message,true)));
}
