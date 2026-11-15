import time
from fastapi import HTTPException
from sqlalchemy import select
from src.models import Product, ConclusionVersion, Job
def create_product(db, data):
    if db.scalar(select(Product).where(Product.name == data.name)):
        raise HTTPException(409, '同名产品已存在')
    p = Product(name=data.name, created_at=time.time())
    db.add(p); db.flush()
    return p
def _issue(db, product_id, job_id, expected_version, request_id, user, kind, source_version_id=None):
    # 行锁串行化同一产品的并发发布；唯一约束(product_id,version)/(product_id,request_id)兜底
    p = db.scalar(select(Product).where(Product.id == product_id).with_for_update())
    if not p: raise HTTPException(404, '产品不存在')
    existing = db.scalar(select(ConclusionVersion).where(ConclusionVersion.product_id == product_id, ConclusionVersion.request_id == request_id))
    if existing: return existing, False  # 同一请求重试，不新增版本
    current = db.get(ConclusionVersion, p.current_version_id) if p.current_version_id else None
    current_no = current.version if current else 0
    if expected_version != current_no:
        raise HTTPException(409, f'现行结论已是第{current_no}版，基于第{expected_version}版的申请已过期，请刷新后重试')
    j = db.get(Job, job_id)
    if not j or j.status != 'completed' or not j.approved:
        raise HTTPException(409, '请先选择已完成且获批准的分析结果')
    v = ConclusionVersion(product_id=product_id, version=current_no + 1, job_id=job_id, kind=kind, source_version_id=source_version_id, request_id=request_id, created_by=user.id, created_at=time.time())
    db.add(v); db.flush()
    p.current_version_id = v.id
    return v, True
def publish(db, product_id, data, user):
    return _issue(db, product_id, data.job_id, data.expected_version, data.request_id, user, 'publish')
def rollback(db, product_id, data, user):
    t = db.get(ConclusionVersion, data.target_version_id)
    if not t or t.product_id != product_id: raise HTTPException(404, '目标历史版本不存在')
    # 回退同样生成新版本，历史链完整可追溯
    return _issue(db, product_id, t.job_id, data.expected_version, data.request_id, user, 'rollback', source_version_id=t.id)
