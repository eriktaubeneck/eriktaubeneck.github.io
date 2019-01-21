#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Erik Taubeneck'
SITENAME = 'skien.cc'
SITEURL = 'https://skien.cc'
THEME = 'pneumatic'
ICONS_PATH = 'images/icons'
STATIC_PATHS = [
    'images',
    'images/icons',
]

PATH = 'content'

TIMEZONE = 'America/New_York'
RELATIVE_URLS = True
DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

DEFAULT_DATE_FORMAT = '%Y-%m-%d'

DISQUS_SITENAME = "skiencc"

SITE_AUTHOR = 'Erik Taubeneck'
TWITTER_USERNAME = '@taubeneck'
BIO_TEXT = (
    'a mathematician, economist, and statistician by schooling, '
    'data scientist/python hacker by trade, and a homebrewer by night, '
    'skien.cc |skīəns| is my blog aimed to track explorations '
    'in all of the above.'
)

SOCIAL_ICONS = [
    ('http://github.com/eriktaubeneck', 'GitHub', 'fa-github'),
    ('https://www.facebook.com/erik.taubeneck', 'Facebook', 'fa-facebook'),
    ('https://www.instagram.com/taubeneck/', 'Instagram', 'fa-instagram'),
    ('http://twitter.com/taubeneck', 'Twitter', 'fa-twitter'),
]

DEFAULT_PAGINATION = 10

ARTICLE_URL = 'blog/{date:%Y}/{date:%m}/{date:%d}/{slug}/'
ARTICLE_SAVE_AS = 'blog/{date:%Y}/{date:%m}/{date:%d}/{slug}/index.html'

ARCHIVES_SAVE_AS = 'archive/index.html'
YEAR_ARCHIVE_SAVE_AS = '{date:%Y}/index.html'
MONTH_ARCHIVE_SAVE_AS = '{date:%Y}/{date:%m}/index.html'
#plugins

PLUGIN_PATHS = ['../pelican-plugins/']
PLUGINS = [
    'assets',
    # 'sitemap',
    'gravatar',
    'neighbors',
    'liquid_tags.img',
    'liquid_tags.video',
    'liquid_tags.include_code',
    # 'liquid_tags.notebook',
]

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

MARKDOWN = {
    'extension_configs': {
        'markdown.extensions.codehilite': {'linenums': None},
        'markdown.extensions.fenced_code': [],
    }
}
