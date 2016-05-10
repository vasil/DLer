#!/usr/bin/env python2.6

import os
import sys
import urllib2
import logging
import optparse
import ConfigParser

config = None

def download(book, location=os.path.join(os.path.dirname(__file__), '..', 
                                                                    'books')):
    """
    """
   
    webFile = None
    base=config.get('gutenberg', 'base')
    format=config.get('formats', 'epub_images')
    url = base % (book, format)
#    headers = {'User-Agent': config.get('user_agent', 'string')}

    try:
#        request = urllib2.Request(url, None, headers)
        webFile = urllib2.urlopen(url)
        logging.info('Downloading %s' % url)
    except urllib2.HTTPError:
        format=config.get('formats', 'epub_no_images')
        url_bak = base % (book, format)
#        request = urllib2.Request(url_bak, None, headers)
        try:
            webFile = urllib2.urlopen(url_bak)
            logging.info('%s failed. Downloading %s' % (url, url_bak))
        except urllib2.HTTPError:
            logging.warning('Both %s and %s failed. Skiping.' % (url, url_bak))
            return

    sys.stdout.write('.');sys.stdout.flush()
    localFile = open(os.path.join(location, (url.split('/')[-1])), 'w')
    localFile.write(webFile.read())
    webFile.close()
    localFile.close()

def main():
    
    _read_config()
    _configure_logger()

    params = optparse.OptionParser(description=config.get('app', 'description'), 
                                   prog=config.get('app', 'prog'),
                                   version=config.get('app', 'version'),
                                   usage=config.get('app', 'usage'))
    params.add_option('--start', '-S', 
                      default=config.get('constrains', 'start'), 
                      help='starting book number')
    params.add_option('--stop', '-s',
                      default=config.get('constrains', 'stop'),
                      help='ending book number')
    options, arguments = params.parse_args()
    
    location = None 
    if len(arguments) == 1:
        location = os.path.join(os.path.dirname(__file__), arguments[0])
    
    logging.info("Starting to download from %s to %s" % (options.start, 
                                                         options.stop))
    for book_id in range(int(options.start), 
                         int(options.stop)+1):
        download(book_id, location)

def _read_config():
    config_path = os.path.join(os.path.dirname(__file__), '..',
                                                          'config', 
                                                          'downloader.conf')
    global config 
    config = ConfigParser.ConfigParser()
    config.read(config_path)

def _configure_logger():
    LOG_FILENAME = os.path.join('..', 'log', 'downloads.log')
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        filename=LOG_FILENAME)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "\nDownloading Interrupted"
