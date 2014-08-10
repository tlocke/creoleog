from django.http import HttpResponseRedirect, HttpResponseBadRequest, Http404
from django.core.exceptions import PermissionDenied
from django.views.generic.simple import direct_to_template
from google.appengine.api import users
from creoleog.models import Blog, Entry, check_creole
from google.appengine.ext.ndb import Key, delete_multi
from django import forms
from django.forms.util import ErrorList

MAX_BLOGS = 100
MAX_ENTRIES = 100


def return_template(request, template_name, template_map):
    guser = users.get_current_user()
    template_map['guser'] = guser
    template_map['request'] = request
    if guser is None:
        template_map['url'] = users.create_login_url(request.get_full_path())
        template_map['url_linktext'] = 'Sign In'
    else:
        template_map['url'] = users.create_logout_url(request.get_full_path())
        template_map['url_linktext'] = 'Sign Out'
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


class CreoleogForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CreoleogForm, self).__init__(*args, label_suffix='', **kwargs)


def home(request):
    guser = users.get_current_user()
    user_blog = None
    if guser is not None:
        guser_key = user_key(guser)
        user_blog = Blog.query(ancestor=guser_key).get()

    blogs = Blog.query().fetch(MAX_BLOGS)
    if user_blog is not None:
        for i, blog in enumerate(list(blogs)):
            if blog.key.parent() == guser_key:
                del blogs[i]

    return return_template(request, 'home.html', {'blogs': blogs})


class CreateBlogForm(CreoleogForm):
    title = forms.CharField(required=True)


def create_blog(request):
    guser = require_current_user()
    parent = user_key(guser)
    blog = Blog.query(ancestor=parent).get()

    if blog is not None:
        return HttpResponseBadRequest("A blog has already been created.")

    if request.method == 'POST':
        form = CreateBlogForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            blog_title = cd['title'].strip()
            duplicate_blog = Blog.query(Blog.title == blog_title).get()
            if duplicate_blog is None:
                if Blog.query().count() >= MAX_BLOGS:
                    errors = form._errors.setdefault("title", ErrorList())
                    errors.append(
                        "Sorry, the maximum number of blogs has been "
                        "reached.")
                else:
                    blog = Blog(title=blog_title, parent=parent)
                    blog.put()
                    return HttpResponseRedirect(
                        '/view_blog?blog_key=' + blog.key.urlsafe())
            else:
                errors = form._errors.setdefault("title", ErrorList())
                errors.append(u"This blog name is already taken.")
    else:
        form = CreateBlogForm()

    return return_template(request, 'create_blog.html', {'form': form})


def view_blog(request):
    blog = get_blog(request.GET)
    entries = Entry.query(
        ancestor=blog.key).order(-Entry.creation_date).fetch(MAX_ENTRIES)
    return return_template(
        request, 'view_blog.html', {'blog': blog, 'entries': entries})


class NewEntryForm(CreoleogForm):
    body = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'cols': '80', 'rows': '20'}),
        validators=[check_creole], label='')


def new_entry(request):
    if request.method == 'POST':
        guser = require_current_user()
        blog = get_blog(request.POST)
        require_blog_owner(guser, blog)
        form = NewEntryForm(request.POST)
        if Entry.query(ancestor=blog.key).count() >= MAX_ENTRIES:
            errors = form._errors.setdefault("body", ErrorList())
            errors.append(
                "Sorry, the maximum number of posts has been "
                "reached.")
        elif form.is_valid():
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


class EditEntryForm(CreoleogForm):
    body = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'cols': '80', 'rows': '20'}),
        validators=[check_creole],
        label='')


def edit_entry(request):
    if request.method == 'POST':
        guser = require_current_user()
        entry = get_entry(request.POST)
        blog = entry.key.parent().get()
        require_blog_owner(guser, blog)
        if 'delete' in request.POST:
            entry.key.delete()
            return HttpResponseRedirect(
                '/view_blog?blog_key=' + blog.key.urlsafe())
        else:
            form = NewEntryForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                entry.body = cd['body']
                entry.put()
                return HttpResponseRedirect(
                    '/view_blog?blog_key=' + blog.key.urlsafe())
    else:
        entry = get_entry(request.GET)
        blog = entry.key.parent().get()
        form = EditEntryForm(initial={'body': entry.body})

    return return_template(
        request, 'edit_entry.html', {
            'blog': blog, 'entry': entry, 'form': form})


class EditBlogForm(CreoleogForm):
    title = forms.CharField(required=True, label='')


def edit_blog(request):
    if request.method == 'POST':
        guser = require_current_user()
        blog = get_blog(request.POST)
        require_blog_owner(guser, blog)
        if 'delete' in request.POST:
            delete_multi(Entry.query(ancestor=blog.key).iter(keys_only=True))
            blog.key.delete()
            return HttpResponseRedirect('/')
        else:
            form = EditBlogForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                blog.title = cd['title']
                blog.put()
                return HttpResponseRedirect(
                    '/view_blog?blog_key=' + blog.key.urlsafe())
    else:
        guser = require_current_user()
        blog = get_blog(request.GET)
        require_blog_owner(guser, blog)
        form = EditBlogForm(initial={'title': blog.title})

    return return_template(
        request, 'edit_blog.html', {'blog': blog, 'form': form})
