from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from GNU_Chess_App import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'GNU_Chess_Online.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', views.home, name='GNU_Chess_Online'),
    url(r'^loginv$', views.login_view, name='Login'),
    url(r'^loginp$', views.login_post, name='Login'),
    url(r'^logout$', views.logout_view, name='Logout'),
	url(r'^signupv$', views.signup_view, name='Sign Up'),
	url(r'^signupp$', views.signup_post, name='Sign Up'),
	url(r'^playv$', views.play_view, name='Play View'),
	url(r'^playp$', views.play_post, name='Play Post'),
	url(r'^new$', views.new, name='New'),
	url(r'^resume$', views.resume, name='Resume'),
	url(r'^savev$', views.save_view, name='Save View'),
	url(r'^savep$', views.save_post, name='Save Post'),
	url(r'^loadv$', views.load_view, name='Load View'),
	url(r'^loadp$', views.load_post, name='Load Post'),
	url(r'^loadpass$', views.load_pass, name='Load Pass'),
)
