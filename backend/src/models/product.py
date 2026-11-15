from sqlalchemy import String, Double, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.config.database import Base
class Product(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    current_version_id: Mapped[int | None] = mapped_column(ForeignKey('conclusion_versions.id'), nullable=True)
    created_at: Mapped[float] = mapped_column(Double)
class ConclusionVersion(Base):
    __tablename__ = 'conclusion_versions'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    version: Mapped[int]
    job_id: Mapped[int] = mapped_column(ForeignKey('jobs.id'))
    kind: Mapped[str] = mapped_column(String(20), default='publish')
    source_version_id: Mapped[int | None] = mapped_column(ForeignKey('conclusion_versions.id'), nullable=True)
    request_id: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[float] = mapped_column(Double)
    __table_args__ = (UniqueConstraint('product_id', 'version'), UniqueConstraint('product_id', 'request_id'))
