from __future__ import unicode_literals, print_function, absolute_import
from flask import Flask, render_template, send_file, request
from gevent.queue import Queue
from gevent.pywsgi import WSGIServer
import os

from ..index import Index, PackageNotFound


class Server(object):
    def __init__(self, args):
        self.args = args
        self.index = Index(args.curddir)
        self.index.scan()

        self.app = Flask(__name__)
        self.app.add_url_rule('/', 'index', self.web_index)
        self.app.add_url_rule('/<query>', 'search', self.web_search)
        self.app.add_url_rule('/<package>', 'upload', self.web_upload,
                              methods=('PUT',))

    def start(self):
        if self.args.debug:
            self.app.run(debug=True)
        else:
            WSGIServer(('0.0.0.0', 8000), self.app).serve_forever()

    def web_index(self):
        return render_template('index.html', index=self.index)

    def web_search(self, query):
        try:
            path = self.index.get(query)
        except PackageNotFound:
            return 'package not found', 404
        except ValueError:
            return 'your query is wrong', 400
        return send_file(
            path, as_attachment=True,
            attachment_filename=os.path.basename(path))

    def web_upload(self, package):
        """
         * Smart enough to not save things we already have
         * Idempotent, you can call as many times as you need
         * The caller names the package (its basename)
        """
        pkg = request.files[package]
        self.index.from_data(package, pkg.read())
        return 'ok'