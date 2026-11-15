import time, json
from sqlalchemy import select, func
from src.config.database import Session
from migrations.initial import migrate
from src.models import User, Dataset, Job, Report, Delivery, Audit, Product, ConclusionVersion
from src.services.business import metadata, seed_records, analyze
from src.services.reports import deliver
from src.utils.security import hash_password
from src.utils.serialization import checksum
def seed():
    migrate()
    with Session() as db:
        for role,name in [('admin','林知 · 业务负责人'),('analyst','陈舟 · 分析员'),('viewer','周禾 · 观察员')]:
            email=role+'@demo.local'
            if not db.scalar(select(User).where(User.email==email)):
                db.add(User(email=email,name=name,role=role,password=hash_password('Demo123!')))
        db.flush()
        m=metadata()
        d=db.scalar(select(Dataset).where(Dataset.name==m['dataset_name']))
        if not d:
            rows=seed_records()
            d=Dataset(name=m['dataset_name'],source=m['short']+'-202611.csv',records=rows,checksum=checksum(rows),created_at=time.time())
            db.add(d); db.flush()
        baseline=db.scalar(select(Job).where(Job.name=='基线复核 · '+m['name']))
        if not baseline:
            params={p['key']:p['default'] for p in m.get('parameters',[])}
            result=analyze(d.records,params)
            json.dumps(result,ensure_ascii=False,allow_nan=False)
            admin=db.scalar(select(User).where(User.role=='admin'))
            baseline=Job(name='基线复核 · '+m['name'],dataset_id=d.id,params=params,status='completed',result=result,created_by=admin.id,created_at=time.time()-3600,finished_at=time.time()-3595,approved=True)
            db.add(baseline);db.flush()
            r=Report(name='每日业务复核简报',job_id=baseline.id,destination='业务复核组 · 本地收件箱',interval_seconds=86400,next_run=time.time()+86400,enabled=True)
            db.add(r);db.flush();deliver(db,r)
            db.add(Audit(actor='seed',action='demo.baseline',detail={'dataset':d.id},at=time.time()))
        if not db.scalar(select(Product).where(Product.name=='反应釜运行窗口 · 工艺结论')):
            admin=db.scalar(select(User).where(User.role=='admin'))
            p=Product(name='反应釜运行窗口 · 工艺结论',created_at=time.time())
            db.add(p);db.flush()
            v=ConclusionVersion(product_id=p.id,version=1,job_id=baseline.id,kind='publish',request_id='seed-baseline-v1',created_by=admin.id,created_at=time.time())
            db.add(v);db.flush()
            p.current_version_id=v.id
            db.add(Report(name='每周工艺结论简报',product_id=p.id,destination='工艺评审组 · 本地收件箱',interval_seconds=604800,next_run=time.time()+3600,enabled=True))
            db.add(Audit(actor='seed',action='demo.product',detail={'product':p.id,'version':1},at=time.time()))
        db.commit()
        counts={model.__tablename__:db.scalar(select(func.count()).select_from(model)) for model in [User,Dataset,Job,Product,ConclusionVersion,Report,Delivery,Audit]}
        print(json.dumps(counts,ensure_ascii=False))
        return counts
if __name__=='__main__':seed()
