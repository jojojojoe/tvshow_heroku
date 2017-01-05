import datetime
import time

print time.asctime()

print datetime.datetime.now()

dramas = [
    {'name': 'House of Cards',
     'description': 'about...',
     'genre_id': 'xx'
     },
    {'name': 'Good wife',
     'description': 'about good wife in ..',
     'genre_id': 'xx'
     }
]
# print dramas[0]['name']

dic = {'a':1, 'b':2}
print '---------'
del dic['a']
print dic