from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from src.config.database import get_db
from src.models import Product, ConclusionVersion
from src.schemas.product import ProductInput, PublishInput, RollbackInput
from src.middlewares.auth import current_user, admin_only
from src.services import conclusions
from src.services.audit import record
from src.utils.serialization import product_dict, version_dict
router=APIRouter(prefix='/products')
@router.get('')
def listing(db=Depends(get_db),u=Depends(current_user)):
    return [product_dict(db,p) for p in db.scalars(select(Product).order_by(Product.id))]
@router.post('',status_code=201)
def create(data:ProductInput,db=Depends(get_db),u=Depends(admin_only)):
    p=conclusions.create_product(db,data); record(db,u.email,'product.create',{'id':p.id,'name':p.name}); db.commit()
    return product_dict(db,p)
@router.get('/{id}/versions')
def versions(id:int,db=Depends(get_db),u=Depends(current_user)):
    if not db.get(Product,id): raise HTTPException(404,'产品不存在')
    return [version_dict(db,v) for v in db.scalars(select(ConclusionVersion).where(ConclusionVersion.product_id==id).order_by(ConclusionVersion.version.desc()))]
@router.post('/{id}/publish',status_code=201)
def publish(id:int,data:PublishInput,db=Depends(get_db),u=Depends(admin_only)):
    v,created=conclusions.publish(db,id,data,u)
    if created: record(db,u.email,'conclusion.publish',{'product':id,'version':v.version,'job':v.job_id})
    db.commit()
    return version_dict(db,v)
@router.post('/{id}/rollback',status_code=201)
def rollback(id:int,data:RollbackInput,db=Depends(get_db),u=Depends(admin_only)):
    v,created=conclusions.rollback(db,id,data,u)
    if created: record(db,u.email,'conclusion.rollback',{'product':id,'version':v.version,'source':v.source_version_id})
    db.commit()
    return version_dict(db,v)
