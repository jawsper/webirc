from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'webirc/index.html'

class ReactTestView(TemplateView):
    template_name = 'webirc/react.html'