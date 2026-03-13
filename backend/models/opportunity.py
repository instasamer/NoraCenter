import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
import enum

from backend.models.database import Base


class Category(str, enum.Enum):
    BECA = "beca"
    RESIDENCIA = "residencia"
    SUBVENCION = "subvencion"
    CONVOCATORIA = "convocatoria"
    EMPLEO = "empleo"
    PREMIO = "premio"
    FORMACION = "formacion"
    EXPOSICION = "exposicion"
    FESTIVAL = "festival"
    OTRO = "otro"


class Discipline(str, enum.Enum):
    ARTES_VISUALES = "artes_visuales"
    MUSICA = "musica"
    TEATRO = "teatro"
    DANZA = "danza"
    CINE = "cine"
    LITERATURA = "literatura"
    FOTOGRAFIA = "fotografia"
    DISENO = "diseno"
    ARTES_DIGITALES = "artes_digitales"
    MULTIDISCIPLINAR = "multidisciplinar"
    OTRO = "otro"


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    category = Column(SAEnum(Category), index=True)
    discipline = Column(SAEnum(Discipline), index=True)

    # Organization / source
    organization = Column(String(300))
    source_name = Column(String(200), nullable=False)
    source_url = Column(String(1000), nullable=False, unique=True)

    # Location
    location = Column(String(300))
    region = Column(String(100), index=True)  # Comunidad autónoma

    # Dates
    deadline = Column(DateTime, index=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    publication_date = Column(DateTime)

    # Financial
    funding_amount = Column(String(200))

    # Metadata
    scraped_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Opportunity {self.title[:50]}>"
