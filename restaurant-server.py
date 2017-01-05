from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

class WebserverHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.endswith('/restaurants'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                restaurants = session.query(Restaurant.id,Restaurant.name).all()
                output = "<html><body><ul>"
                for r in restaurants:
                    output += '<li>%s' % r[1]
                    output += ' <a href="/%s/edit">[Edit] </a><a href="/%s/delete">[Delete]</a>' % (r[0],r[0])
                output += "</li><br></ul><br><br><a href='restaurants/new'>Create New Restaurant</a></body></html>"
                self.wfile.write(output)
                print output

            elif self.path.endswith('restaurants/new'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = '<html><body>'
                output += '<h1>Make a New Restaurant</h1>'
                output += '''<form method="post" enctype="multipart/form-data" action="/restaurants">
                                <input name="newrestaurant" type="text" placeholder="New Restaurant Name">
                                <input type="submit" value="Create"></form>'''
                output += '</body></html>'
                self.wfile.write(output)
                print output

            elif self.path.endswith('/edit'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                id = int(self.path.split('/')[1])
                q = session.query(Restaurant.name).filter_by(id = id).one()[0]

                output = '<html><body><form method="post" enctype="multipart/form-data" action="/restaurantslll"><h2>%s</h2><input type="text" name="editrestaurant">' % q
                output += '<input type="hidden" name="id" value="%s"><input type="submit" value="Update"></form></body></html>' % id
                self.wfile.write(output)

            elif self.path.endswith('/delete'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                id = int(self.path.split('/')[1])
                q = session.query(Restaurant.name).filter_by(id = id).one()[0]

                output = '<html><body><h1>Are you sure your want to delete \' %s \'' % q
                output += ' ? </h1>'
                output += '<form method="post" enctype="multipart/form-data" action="/restaurants">'
                output += '<input type="hidden" name="deleteid" value="%s">' % id
                output += '<input type="submit" value="Delete">'
                output += '</form></body></html>'
                self.wfile.write(output)
        except IOError:
            self.send_error(404, 'File Not Found %s' % self.path)

    def do_POST(self):
        # self.send_response(301)
        # self.end_headers()


        # my version is the hard way to acomplishe this,
        # on the hidden input, actualy can just get the id 
        # from url like the do_GET() methods
        # self.path.endswith('/9/edit') ../9/delete
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        if ctype == 'multipart/form-data':
            fields = cgi.parse_multipart(self.rfile, pdict)
            print fields,'fields ^^^^^^'

            if 'newrestaurant' in fields:
                name = fields.get('newrestaurant')[0]
                restaurant = Restaurant(name=name)
                session.add(restaurant)
                session.commit()

            elif 'editrestaurant' in fields:
                name = fields.get('editrestaurant')[0]
                id = fields.get('id')[0]
                restaurant = session.query(Restaurant).filter_by(id=int(id)).one()
                restaurant.name = name
                session.add(restaurant)
                session.commit()
            elif 'deleteid' in fields:
                id = fields.get('deleteid')[0]
                restaurant = session.query(Restaurant).filter_by(id=int(id)).one()
                session.delete(restaurant)
                session.commit()
                print 'deleted, ^^^^^,', id, restaurant


            # restaurants = session.query(Restaurant.id,Restaurant.name).all()
            # output = "<html><body><ul>"
            # for r in restaurants:
            #     output += '<li>%s' % r[1]
            #     output += ' <a href="/%s/edit">[Edit] </a><a href="/%s/delete">[Delete]</a>' % (r[0],r[0])
            # output += "</li><br></ul><br><br><a href='restaurants/new'>Create New Restaurant</a></body></html>"
            # self.wfile.write(output)
            # print output

        self.send_response(301)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', '/restaurants')
        self.end_headers()



def main():
    try:
        port = 8080
        server = HTTPServer(('', port), WebserverHandler)
        print 'Web server is running on port %s' % port
        server.serve_forever()
    except KeyboardInterrupt:
        print "^C entered, stopping server"

if __name__ == '__main__':
    main()

