"""Tornado handlers for the live notebook view."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import shutil
import os
import io
from tornado import web
HTTPError = web.HTTPError

from ..base.handlers import (
    IPythonHandler, FilesRedirectHandler,
    notebook_path_regex, path_regex,
)
from ..utils import url_escape


class NotebookHandler(IPythonHandler):

    @web.authenticated
    def get(self, path='', name=None):
        """get renders the notebook template if a name is given, or 
        redirects to the '/files/' handler if the name is not given."""
        path = path.strip('/')
        cm = self.contents_manager

        parts = self.request.uri.split('/')
        if 'templates' == parts[1]:
            filename = '/'.join(parts[2:])
            to_filename = filename.replace('.tpl', '{}.ipynb')
            i = 0
            while os.path.exists(to_filename.format(i)):
                i += 1
            to_filename = to_filename.format(i)

            shutil.copyfile(filename, to_filename)
            redirect = '../notebooks/' + to_filename
            self.redirect(redirect)
            return

        if name is None:
            raise web.HTTPError(500, "This shouldn't be accessible: %s" % self.request.uri)
        
        # a .ipynb filename was given
        if not cm.file_exists(name, path):
            raise web.HTTPError(404, u'Notebook does not exist: %s/%s' % (path, name))
        name = url_escape(name)
        path = url_escape(path)
        self.write(self.render_template('notebook.html',
            notebook_path=path,
            notebook_name=name,
            kill_kernel=False,
            mathjax_url=self.mathjax_url,
            )
        )


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r"/notebooks%s" % notebook_path_regex, NotebookHandler),
    (r"/notebooks%s" % path_regex, FilesRedirectHandler),
    (r"/templates%s" % path_regex, NotebookHandler),
]

