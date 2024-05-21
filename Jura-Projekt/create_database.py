from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Stvaranje engine-a za SQLite bazu
engine = create_engine('sqlite:///jobs.db')

# Bazna klasa za deklarativno definiranje ORM modela
Base = declarative_base()

# Definicija ORM modela za tablicu Lokacijeclass Lokacija(Base):
class Lokacija(Base):
    __tablename__ = 'lokacije'
    geoID = Column(Integer, primary_key=True)
    geoName = Column(String)
    geoSlug = Column(String)
    poslovi = relationship('Posao', back_populates='lokacija')

class Posao(Base):
    __tablename__ = 'poslovi'
    id = Column(Integer, primary_key=True)
    naziv = Column(String)
    opis = Column(String)
    lokacija_id = Column(Integer, ForeignKey('lokacije.geoID'))
    lokacija = relationship('Lokacija', back_populates='poslovi')
    industrija_id = Column(Integer, ForeignKey('industrije.industryID'))  # Ispravljeno
    industrija = relationship('Industrija', back_populates='poslovi')
    naslov = Column(String)  # Ispravljeno
    link = Column(String)
    image_url= Column(String)
class Industrija(Base):
    __tablename__ = 'industrije'
    industryID = Column(Integer, primary_key=True)  # Ispravljeno
    industryName = Column(String)  # Ispravljeno
    industrySlug = Column(String)
    poslovi = relationship('Posao', back_populates='industrija')
# Stvaranje tablica u bazi
Base.metadata.create_all(engine)

# Stvaranje sesije
Session = sessionmaker(bind=engine)
session = Session()
