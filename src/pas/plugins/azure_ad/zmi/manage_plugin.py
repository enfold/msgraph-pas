# -*- coding: utf-8 -*-
from Products.Five import BrowserView


class ManageAzureADPlugin(BrowserView):

    @property
    def plugin(self):
        return self.context

    def next(self, request):
        return '%s/manage_azure_ad_plugin' % self.context.absolute_url()
