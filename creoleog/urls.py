from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^edit_blog$', 'creoleog.views.edit_blog'),
    url(r'^edit_entry$', 'creoleog.views.edit_entry'),
    url(r'^new_entry$', 'creoleog.views.new_entry'),
    url(r'^view_blog$', 'creoleog.views.view_blog'),
    url(r'^create_blog$', 'creoleog.views.create_blog'),
    url(r'^$', 'creoleog.views.home'),
    # url(r'^creoleog/', include('creoleog.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
