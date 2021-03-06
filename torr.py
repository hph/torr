#/usr/bin/python
#coding=utf8

import argparse
import HTMLParser
import os
import re
import sys
import time
import urllib2


def unescape(string):
    '''Return HTML unescaped string.'''
    string = string.decode('utf8')
    return HTMLParser.HTMLParser().unescape(string)


def get_html(movie, index=0):
    '''Return a list with each line of the search results HTML code for movie
    from The Pirate Bay.'''
    head = 'http://thepiratebay.se/search/'
    tail = '/%s/7/0' % index
    # TODO Replace other characters. Use the library functions instead.
    movie = movie.replace(' ', '%20')
    return urllib2.urlopen(head + movie + tail).readlines()


def parse_html(html):
    '''Return a list containing data parsed from the HTML code.'''
    data = []
    results = []
    for i, line in enumerate(html):
        if '<td class="vertTh">' in line:
            results.append(html[i:i + 14])
    for result in results:
        # Start of ugly and unreadable (but working) regex piece of shit code.
        type = re.match(r'(.*) category">(.*)', result[2], re.M).group(2)[:-10]
        cat = re.match(r'(.*) category">(.*)', result[3], re.M).group(2)[:-5]
        name = re.match(r'(.*)">(.*)', result[7], re.M).group(2)[:-4]
        url = re.match(r'(.*)class="detLink"(.*)',
                       re.match(r'(.*)<a href=(.*)', result[7], re.M).group(2),
                       re.M).group(1)[1:-2]
        magnet = result[9].split(' title')[0][9:-1]
        date = re.match(r'(.*)Uploaded (.*)', result[10],
                        re.M).group(2).split(', ')[0]
        size = re.match(r'(.*), (.*)',
                        re.match(r'(.*) Size (.*)', result[10], re.M).group(2),
                        re.M).group(1)
        seeds = re.match(r'(.*)"right">(.*)', result[12], re.M).group(2)[:-5]
        leeches = re.match(r'(.*)"right">(.*)', result[13], re.M).group(2)[:-5]
        # End of regex piece of shit code.
        data.append({'name': unescape(name),
                     'url': 'http://thepiratebay.se%s' % url,
                     'magnet': magnet,
                     'size': unescape(size),
                     'seeds': seeds,
                     'leeches': leeches,
                     'date': unescape(date),
                     'type': type,
                     'cat': cat})
    return data


def repr_data(data):
    '''Print items in data.'''
    for index, torrent in enumerate(data):
        index = '[%s]' % str(index + 1)
        seeds_leeches = '%s/%s' % (torrent['seeds'], torrent['leeches'])
        seeds_leeches = seeds_leeches.ljust(12)
        size = torrent['size'].ljust(12)
        print '%s%s%s%s (%s)' % (index.ljust(6), seeds_leeches, size,
                                         torrent['name'], torrent['date'])


def repr_torrent(torrent, watching=False):
    '''Print detailed information about torrent.'''
    print
    print 'Torrent name:  %s' % torrent['name']
    print 'Type/category: %s/%s' % (torrent['type'], torrent['cat'])
    print 'Seeds/leeches: %s/%s' % (torrent['seeds'], torrent['leeches'])
    print 'Size:          %s' % torrent['size']
    print 'Torrent url:   %s' % torrent['url']
    print 'Magnet link:   %s' % torrent['magnet']
    if watching:
        return
    message = '\nEnter d to download or press Enter to dismiss: '
    action = raw_input(message)
    if len(action) == 0:
        sys.exit()
    elif action == 'd':
        # Requires a settings file called conf in the same directory.
        with open('conf', 'r') as conf:
            conf = [line.split(':') for line in conf]
        for setting in conf:
            if setting[0] == 'torr_prog_path':
                call = '%s %s' % (setting[1].strip(), torrent['magnet'])
                os.system(call)


def watch(data, query, seconds=30):
    '''Recheck every few seconds whether a torrent is available and notify if
    it is available.'''
    while True:
        os.system('clear')
        if len(data) > 0:
            dates = ', '.join([torrent['date'] for torrent in data])
            s = '' if len(data) < 2 else 's'
            print '%s torrent%s found from %s.' % (len(data), s, dates)
            for torrent in data:
                repr_torrent(torrent, True)
        else:
            print 'No torrent found.'
        time.sleep(seconds)
        os.system('clear')
        print 'Checking anew.'
        data = parse_html(get_html(query))


def parse_args():
    '''Set arguments and return parsed arguments.'''
    # TODO Design an interface. We have the data retrieval functions, all
    # that's left is to write the interface itself.
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--watch', action='store_true',
                        help='''Print a list of torrents available if any.''')
    parser.add_argument('-t', '--text', action='store_true',
                        help='''Only print a list of torrents available.''')
    parser.add_argument('query',
                        help='''Search query.''')
    parser.add_argument('index', nargs='?', default=0,
                        help='''Search query page index. Default is 0.''')
    return parser.parse_args()


def main():
    # NOTE This is temporary and only for testing purposes.
    # TODO Create a download function.
    # TODO Get data from torrent url.
    # TODO Create a settings file and a parse settings function.
    # TODO Add filtering options - only show HD etc and rank torrents based on
    # the size, the name (contains 720p/1080p/BluRay?) and the number of seeds.
    # TODO Add option to select the best torrent and download it.
    args = parse_args()
    html = get_html(args.query, args.index)
    data = parse_html(html)
    if args.watch:
        watch(data, args.query)
    try:
        repr_data(data)
        msg = '\nEnter a number (1-30) for details or press Enter to dismiss: '
        now = '0'
        if not args.text:
            now = raw_input(msg)
        if len(now) == 0:
            sys.exit()
        elif int(now) in range(1, 31):
            repr_torrent(data[int(now) - 1])
    except KeyboardInterrupt:
        print
        sys.exit()


if __name__ == '__main__':
    main()
