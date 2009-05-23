'''
A simple shared task list.
Fields: Done Checkbox, Action, Who, When. (Delete | Edit)
Sortable. Filterable checkbox. Search as you type.
New line to add things at the end. Dates can be entered in GNU format. Who is an autocompletion list like Excel. Enter adds item and creates a new box.

task.s-anand.net/payments

TODO:
# Multiple filters do not work now
# done checkbox filter
# Show loading indicator for done button
# Fix the date format string
'''

import wsgiref.handlers, urllib, datetime
from datetime                             import date
from google.appengine.ext                 import webapp, db
from google.appengine.api                 import users
from google.appengine.ext.webapp          import template

class Task(db.Model):
    name = db.StringProperty    (required=True)                         # Name of the list this task is in
    time = db.DateTimeProperty  (required=True, auto_now_add=True)      # Last modified date
    user = db.UserProperty      (required=True, auto_current_user=True) # User who last modified this
    what = db.StringProperty    (required=True)                         # What's the task
    who  = db.StringProperty    ()                                      # Who has to do the task (need not be another user on the system)
    when = db.DateProperty      ()                                      # When is the task is due
    done = db.BooleanProperty   (default=False)                         # Task accomplished or not

class Access(db.Model):
    name = db.StringProperty    (required=True)                         # Name of the list
    user = db.StringProperty    (required=True)                         # e-mail IDs of user who can access this list
    time = db.DateTimeProperty  (required=True, auto_now_add=True)      # Last modified date

user = users.get_current_user()

class ListPage(webapp.RequestHandler):
    def get(self, name):
        if not user:                                                                            # if user not logged in, send to login page
            self.redirect('/login/' + name)
        elif Access.all().filter('name = ', name).filter('user = ', user.email()).count() <= 0: # If no permission, say so
            self.response.out.write('No access for ' + user.email())
        else:
            tasks = Task.all().filter('name = ', name).order('when')
            mobile = self.request.headers['User-Agent'].find('BlackBerry') >= 0 and 1 or 0
            self.response.out.write(template.render('index.html', dict(locals().items() + globals().items())))

    def post(self, name):
        if user and Access.all().filter('name = ', name).filter('user = ', user.email()).count() > 0:
            if self.request.get('action') == 'add_task':
                what, who, when = (self.request.get(x) for x in ('what', 'who', 'when'))
                when = date.fromtimestamp(float(when)/1000 + 43200.0)
                task = Task(name=name, what=what, who=who, when=when)
                task.put()
                self.response.out.write('200 OK\t' + str(task.key()))

            elif self.request.get('action') == 'del_task':
                key = self.request.get('key')
                task = Task.get(key)
                if task:
                    task.delete()
                    self.response.out.write('200 OK\t' + key)
                else:
                    self.response.out.write('404 Key not found ' + key)

            elif self.request.get('action') == 'edit_task':
                key, what, who, when = (self.request.get(x) for x in ('key', 'what', 'who', 'when'))
                when = date.fromtimestamp(float(when)/1000 + 43200.0)
                task = Task.get(key)
                if task:
                    task.what = what
                    task.who  = who
                    task.when = when
                    task.put()
                    self.response.out.write('200 OK\t' + key)
                else:
                    self.response.out.write('404 Key not found ' + key)

            elif self.request.get('action') == 'do_task':
                key, value = self.request.get('key'), self.request.get('value')
                task = Task.get(key)
                if task:
                    if value == '1': task.done = True
                    else:            task.done = False
                    task.put()
                    self.response.out.write('200 OK\t' + key)
                else:
                    self.response.out.write('404 Key not found ' + key)

# /_add/listname/email will add email to listname
class AddUserPage(webapp.RequestHandler):
    def get(self, name, person):
        if users.is_current_user_admin():
            person = urllib.unquote(person)
            Access(name=name, user=person).put()
            self.response.out.write('Added ' + person + ' to list: ' + name)

class LoginPage(webapp.RequestHandler):
    def get(self, name): self.redirect(users.create_login_url('/' + name))

class LogoutPage(webapp.RequestHandler):
    def get(self): self.redirect(users.create_logout_url('/'))

application = webapp.WSGIApplication([
        ('/login/(.+)',     LoginPage),
        ('/logout',         LogoutPage),
        ('/_add/(.+)/(.+)', AddUserPage),
        ('/(.+)',           ListPage),
    ],
    debug=True)
wsgiref.handlers.CGIHandler().run(application)
