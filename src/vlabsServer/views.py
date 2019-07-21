from django.views.generic.base import TemplateView, RedirectView


class Home(RedirectView):
    # template_name = "home.html"
    url = '/admin'


