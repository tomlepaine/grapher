from glob import glob
import argparse
import os

from bottle import get, post, run, response, request, static_file, redirect
from jinja2 import Environment, PackageLoader
import numpy
import yaml

import config

parser = argparse.ArgumentParser(prog=config.name,
                                 description=config.description)

parser.add_argument('--port',
                    type=int,
                    default=8080,
                    help='Port where gui is running.')

parser.add_argument('--path',
                    type=str,
                    help='Path for yml file.')

args = parser.parse_args()

PORT = args.port

ENV = Environment(loader=PackageLoader(config.package_name,
                                       config.template_dir))


with open(args.path, 'r') as f:
    arg_dict = yaml.load(f)


class Page(object):
    def __init__(self):
        self.template = ENV.get_template('base.html')
        self.sections = []
        self.count = 0
        self.contents = []

    def add_section(self, name, data, template):
        section_template = ENV.get_template(template)
        section = section_template.render(number=self.count,
                                          name=name,
                                          data=data)
        self.sections.append(section)
        self.count += 1
        self.contents.append(name)

    def render(self):
        page = self.template.render(contents=self.contents,
                                    sections=self.sections)
        return page


def get_first(pattern):
    results = glob(pattern)
    sorted_results = numpy.sort(results)
    return sorted_results[0]


def get_last(pattern):
    results = glob(pattern)
    if results:
        sorted_results = numpy.sort(results)
        last = sorted_results[-1]
    else:
        last = 'http://placehold.it/800x600?text=not found'
    return last


def get_lasts(root, jobs, pattern):
    for job in jobs:
        full_pattern = os.path.join(root, job['dir'], pattern)
        last = get_last(full_pattern)
        yield last


def clean(data, root):
    return [datum.replace(root, '/static/') for datum in data]


def last_data(arg_dict, pattern):
    root = arg_dict['root']
    jobs = arg_dict['jobs']
    names = [job['name'] for job in jobs]
    urls = clean(get_lasts(root, jobs, pattern), root)

    data = []
    for name, url in zip(names, urls):
        datum = {}
        datum['name'] = name
        datum['url'] = url
        data.append(datum)

    return data


@get('/')
def index():
    results = arg_dict['results']

    page = Page()

    for result in results:
        name = result['name']
        pattern = result['pattern']
        data = last_data(arg_dict, pattern)
        page.add_section(name=name,
                         data=data,
                         template='images.html')

    return page.render()


@get('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=arg_dict['root'])

run(host='localhost', port=PORT)
