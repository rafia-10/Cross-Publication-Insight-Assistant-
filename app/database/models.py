from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    source_url = Column(String, unique=True, index=True)
    source_type = Column(String)  # "github" or "publication"
    description = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    technologies = relationship("ProjectTechnology", back_populates="project", cascade="all, delete-orphan")
    evidences = relationship("Evidence", back_populates="project", cascade="all, delete-orphan")
    vector_records = relationship("VectorRecord", back_populates="project", cascade="all, delete-orphan")

class Technology(Base):
    __tablename__ = "technologies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)
    
    # Relationship to associative table
    projects = relationship("ProjectTechnology", back_populates="technology")

class ProjectTechnology(Base):
    __tablename__ = "project_technologies"
    
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    technology_id = Column(Integer, ForeignKey("technologies.id"), primary_key=True)
    confidence = Column(String, nullable=True) # E.g., 'high', 'medium', 'low'
    evidence_json = Column(JSON, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="technologies")
    technology = relationship("Technology", back_populates="projects")

class Evidence(Base):
    __tablename__ = "evidences"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    file_path = Column(String)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    text = Column(Text)
    
    # Relationship
    project = relationship("Project", back_populates="evidences")

class VectorRecord(Base):
    __tablename__ = "vector_records"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    chunk_text = Column(Text)
    file_path = Column(String)
    chroma_id = Column(String, unique=True, index=True)
    
    # Relationship
    project = relationship("Project", back_populates="vector_records")
