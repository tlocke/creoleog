from google.appengine.ext import ndb

class Blog(ndb.Model):
    title = ndb.StringProperty(required=True, indexed=False)

class Entry(ndb.Model):
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
