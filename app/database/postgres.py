from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.database.models import Base, Project, Technology, ProjectTechnology

# Create the engine based on the config. 
# Defaults to sqlite:///./insight.db if not specified
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper CRUD functions
def get_project_by_url(db: Session, source_url: str) -> Optional[Project]:
    return db.query(Project).filter(Project.source_url == source_url).first()

def get_technology_by_name(db: Session, name: str, category: str) -> Technology:
    tech = db.query(Technology).filter(Technology.name == name, Technology.category == category).first()
    if not tech:
        tech = Technology(name=name, category=category)
        db.add(tech)
        db.commit()
        db.refresh(tech)
    return tech
