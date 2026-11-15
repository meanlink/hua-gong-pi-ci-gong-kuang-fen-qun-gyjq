import time, os, csv, io, hashlib, json
from fastapi import HTTPException
from src.models import Job, Report, Delivery, Product, ConclusionVersion
from src.config.settings import ARTIFACT_DIR
def create(db, data):
    if bool(data.job_id) == bool(data.product_id):
        raise HTTPException(422, '固定分析与订阅产品需且只能选一个')
    if data.job_id:
        j=db.get(Job,data.job_id)
        if not j or j.status!='completed' or not j.approved:
            raise HTTPException(409,'请先选择已完成且获批准的分析结果')
    if data.product_id and not db.get(Product,data.product_id):
        raise HTTPException(404,'订阅的产品不存在')
    r=Report(name=data.name, job_id=data.job_id, product_id=data.product_id, destination=data.destination, interval_seconds=data.interval_seconds, next_run=time.time()+data.delay_seconds, enabled=True)
    db.add(r); db.flush()
    return r
def _archive(db, report, j, version=None, product=None):
    out=io.StringIO()
    out.write('\ufeff')
    table=j.result.get('table',{})
    cols=table.get('columns',[])
    writer=csv.writer(out)
    def safe(v):
        if isinstance(v,(int,float)) and not isinstance(v,bool): return v
        text=str(v)
        return "'"+text if text.startswith(('=','+','-','@','\t','\r')) else text
    writer.writerow([safe(c['label']) for c in cols])
    for row in table.get('rows',[]): writer.writerow([safe(row.get(c['key'],'')) for c in cols])
    data=out.getvalue().encode('utf-8')
    delivery=Delivery(report_id=report.id, created_at=time.time(), checksum=hashlib.sha256(data).hexdigest(), filename='', destination=report.destination, conclusion_version_id=version.id if version else None)
    db.add(delivery); db.flush()
    delivery.filename=f'report-{report.id}-delivery-{delivery.id}.csv'
    os.makedirs(ARTIFACT_DIR,exist_ok=True)
    with open(os.path.join(ARTIFACT_DIR,delivery.filename),'wb') as f:f.write(data)
    meta={'job':j.name,'params':j.params,'result':j.result,'checksum':delivery.checksum}
    if version: meta['conclusion']={'product':product.name if product else '', 'version':version.version, 'kind':version.kind}
    with open(os.path.join(ARTIFACT_DIR,delivery.filename+'.json'),'w') as f: json.dump(meta,f,ensure_ascii=False,allow_nan=False)
    return delivery
def deliver(db, report):
    if report.product_id:
        if not report.pending_version_id:
            # 期次开始：固定届时现行版本；先提交，确保失败后重试不改换内容
            p=db.get(Product,report.product_id)
            if not p or not p.current_version_id:
                report.next_run=time.time()+report.interval_seconds  # 未发布产品不出刊
                return None
            report.pending_version_id=p.current_version_id
            db.commit()
        v=db.get(ConclusionVersion,report.pending_version_id)
        j=db.get(Job,v.job_id) if v else None
        if not v or not j or not j.approved:
            report.pending_version_id=None
            report.next_run=time.time()+report.interval_seconds
            return None
        d=_archive(db,report,j,v,db.get(Product,report.product_id))
        report.pending_version_id=None
        report.next_run=time.time()+report.interval_seconds
        return d
    j=db.get(Job,report.job_id)
    if not j or not j.approved: return
    d=_archive(db,report,j)
    report.next_run=time.time()+report.interval_seconds
    return d
