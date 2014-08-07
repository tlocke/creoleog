from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.views.generic.simple import direct_to_template
from google.appengine.api import users
from creoleog.models import Blog, Entry
from google.appengine.ext.ndb import Key, delete_multi
import urllib
from django import forms

def return_template(request, template_name, template_map):
    guser = users.get_current_user()
    template_map['guser'] = guser
    template_map['request'] = request
    if guser is None:
        template_map['url'] = users.create_login_url(request.get_full_path())
        template_map['url_linktext'] = 'Login'
    else:
        template_map['url'] = users.create_logout_url(request.get_full_path())
        template_map['url_linktext'] = 'Logout'
        template_map['user_blog'] = Blog.query(ancestor=user_key(guser)).get()

    return direct_to_template(request, template_name, template_map)

def user_key(user):
    return Key('User', user.user_id())

def get_key(params, name):
    try:
        key_str = params[name + '_key']
    except KeyError:
        return HttpBadRequest("Parameter " + name + " is required.")
    return Key(urlsafe=key_str)

def require_current_user():
    guser = users.get_current_user()
    if guser is None:
        return HttpResponseForbidden("You must be logged in to do that.")
    return guser

def require_blog_owner(guser, blog):
    if blog.key.parent() != user_key(guser):
        return HttpResponseForbidden("You can only do that with your blog.")

def home(request):
    guser = users.get_current_user()
    user_blog = None
    if guser is not None:
        guser_key = user_key(guser)
        user_blog = Blog.query(ancestor=guser_key).get()

    blogs = Blog.query().fetch(100)
    if user_blog is not None:
        for i, blog in enumerate(list(blogs)):
            if blog.key.parent() == guser_key:
                del blogs[i]

    return return_template(request, 'home.html', {'blogs': blogs})

class CreateBlogForm(forms.Form):
    title = forms.CharField(required=True)

def create_blog(request):
    guser = require_current_user()

    blog = Blog.query(ancestor=user_key(guser)).get()

    if blog is not None:
        return HttpResponseBadRequest("A blog has already been created.")
        
    if request.method == 'POST':
        form = CreateBlogForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            blog = Blog(title=cd['title'], parent=user_key(guser))
            blog.put()
            return HttpResponseRedirect(
                '/view_blog?blog_key=' + blog.key.urlsafe())
    else:
        form = CreateBlogForm()

    return return_template( request, 'create_blog.html', {'form': form})

def view_blog(request):
    if request.method == 'POST':
        guser = require_current_user()
        blog_key = get_key(request.POST, 'blog')
        blog = blog_key.get()
        require_blog_owner(guser, blog)
        delete_multi(Entry.query(ancestor=blog.key).iter(keys_only=True))
        blog_key.delete()
        return HttpResponseRedirect('/')
    else:
        blog_key = get_key(request.GET, 'blog')
        blog = blog_key.get()
        return return_template(request, 'view_blog.html', {'blog': blog})
