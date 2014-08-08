from django.http import HttpResponseRedirect, HttpResponseBadRequest, Http404
from django.core.exceptions import PermissionDenied
from django.views.generic.simple import direct_to_template
from google.appengine.api import users
from creoleog.models import Blog, Entry, check_creole
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

def get_entity(params, name):
    try:
        key_str = params[name + '_key']
    except KeyError:
        raise Http404("Parameter " + name + " is required.")
    entity = Key(urlsafe=key_str).get()
    if entity is None:
        raise Http404("Can't find this entity.")
    return entity

def get_blog(params):
    blog = get_entity(params, 'blog')
    if blog.key.kind() != 'Blog':
        raise Http404("This isn't the key for a blog.")
    return blog

def get_entry(params):
    entry = get_entity(params, 'entry')
    if entry.key.kind() != 'Entry':
        raise Http404("This isn't the key for a entry.")
    return entry

def require_current_user():
    guser = users.get_current_user()
    if guser is None:
        raise PermissionDenied("You must be logged in to do that.")
    return guser

def require_blog_owner(guser, blog):
    if blog.key.parent() != user_key(guser):
        raise PermissionDenied("You can only do that with your blog.")

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
        blog = get_blog(request.POST)
        require_blog_owner(guser, blog)
        delete_multi(Entry.query(ancestor=blog.key).iter(keys_only=True))
        blog.key.delete()
        return HttpResponseRedirect('/')
    else:
        blog = get_blog(request.GET)
        entries = Entry.query(
            ancestor=blog.key).order(Entry.creation_date).fetch(100)
        return return_template(
            request, 'view_blog.html', {'blog': blog, 'entries': entries})


class NewEntryForm(forms.Form):
    body = forms.CharField(
        required=True, widget=forms.Textarea, validators=[check_creole])

def new_entry(request):
    if request.method == 'POST':
        guser = require_current_user()
        blog = get_blog(request.POST)
        require_blog_owner(guser, blog)
        form = NewEntryForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            entry = Entry(body=cd['body'], parent=blog.key)
            entry.put()
            return HttpResponseRedirect(
                '/view_blog?blog_key=' + blog.key.urlsafe())
    else:
        blog = get_blog(request.GET)
        form = NewEntryForm()

    return return_template(
        request, 'new_entry.html', {'blog': blog, 'form': form})

class EditEntryForm(forms.Form):
    body = forms.CharField(
        required=True, widget=forms.Textarea, validators=[check_creole])

def edit_entry(request):
    if request.method == 'POST':
        guser = require_current_user()
        entry = get_entry(request.POST)
        blog = entry.key.parent().get()
        require_blog_owner(guser, blog)
        form = NewPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            entry = Entry(body=cd['body'], parent=blog.key)
            entry.put()
            return HttpResponseRedirect(
                '/view_blog?blog_key=' + blog.key.urlsafe())
    else:
        entry = get_entry(request.GET)
        blog = entry.key.parent().get()
        form = EditEntryForm()

    return return_template(
        request, 'edit_entry.html', {
            'blog': blog, 'entry': entry, 'form': form})
