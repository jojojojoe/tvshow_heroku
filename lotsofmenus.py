from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Genre, TVShow, User, Base

engine = create_engine('sqlite:///tvshows.db')

# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


user = User(name='Joe', email='joe@xx.com')

genre_names = ['Drama', 'Comedy', 'Family', 'Crime']
for genre_name in genre_names:
    genre = Genre(name=genre_name)
    user_id = user.id
    session.add(genre)
    session.commit()

drama_id = session.query(Genre).filter_by(name='Drama').one().id
drama = session.query(Genre).filter_by(name='Drama').one()

dramas = [
    {'name': 'House of Cards',
     'description': 'about...',
     'genre_id': drama_id
     },
    {'name': 'Good wife',
     'description': 'about good wife in ..',
     'genre_id': drama_id,
     'genre': drama
     }
]

for drama in dramas:
    d = TVShow(name=drama['name'], description=drama['description'], genre_id=drama['genre_id'])
    session.add(d)
    session.commit()
