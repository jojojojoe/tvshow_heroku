import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, func, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Genre(Base):
    __tablename__ = 'genre'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    created_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())

    @property
    def serialize(self):
        return {
        'id':self.id,
        'name':self.name,
        'created_time':self.created_time
        }


class TVShow(Base):
    __tablename__ = 'tvshow'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    img_url = Column(String(250))
    genre_id = Column(Integer, ForeignKey('genre.id'))
    genre = relationship(Genre)
    created_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'img_url': self.img_url,
            'genre': self.genre.name,
            'created_time': self.created_time
        }



engine = create_engine('sqlite:///tvshows.db')

# drop all table before created if schemes are changed 
# or something, for testing 
# User.__table__.drop(engine)
# TVShow.__table__.drop(engine)
# Genre.__table__.drop(engine)

Base.metadata.create_all(engine)
