import hashlib, json
from src.models import ConclusionVersion, Product, Job, User
def checksum(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()
def dataset_dict(d):
    return {'id':d.id, 'name':d.name, 'source':d.source, 'rows':len(d.records), 'checksum':d.checksum, 'created_at':d.created_at}
def job_dict(j):
    return {k:getattr(j,k) for k in ['id','name','dataset_id','params','status','result','error','approved','created_at','finished_at']}
def report_dict(r):
    return {k:getattr(r,k) for k in ['id','name','job_id','product_id','destination','interval_seconds','next_run','enabled']}
def delivery_dict(d):
    return {k:getattr(d,k) for k in ['id','report_id','created_at','checksum','filename','destination','conclusion_version_id']}
def version_dict(db,v):
    j=db.get(Job,v.job_id)
    u=db.get(User,v.created_by)
    return {'id':v.id,'product_id':v.product_id,'version':v.version,'job_id':v.job_id,'job_name':j.name if j else '','kind':v.kind,'source_version_id':v.source_version_id,'created_by':u.name if u else '','created_at':v.created_at}
def product_dict(db,p):
    current=db.get(ConclusionVersion,p.current_version_id) if p.current_version_id else None
    return {'id':p.id,'name':p.name,'created_at':p.created_at,'current_version':version_dict(db,current) if current else None}
