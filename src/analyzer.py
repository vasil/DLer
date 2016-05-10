#!/usr/bin/python2.6

import os
import csv
import uuid
import zipfile
import logging
import optparse


try:
    from lxml import etree
except ImportError:
    import sys
    sys.exit('This program depends on lxml. Please install it first.')

def get_epub_info(fname):
    ns = {
        'n':'urn:oasis:names:tc:opendocument:xmlns:container',
        'pkg':'http://www.idpf.org/2007/opf',
        'dc':'http://purl.org/dc/elements/1.1/'
    }

    zip = zipfile.ZipFile(fname)
    txt = zip.read('META-INF/container.xml')
    tree = etree.fromstring(txt)
    cfname = tree.xpath('n:rootfiles/n:rootfile/@full-path',namespaces=ns)[0]
    cf = zip.read(cfname)
    tree = etree.fromstring(cf)
    p = tree.xpath('/pkg:package/pkg:metadata',namespaces=ns)[0]

    res = {}
    for s in ['title','language','creator','date','identifier']:
        res[s] = p.xpath('dc:%s/text()'%(s),namespaces=ns)[0]

    return res


def main():
    _configure_logger()
    params = optparse.OptionParser(description='', 
                                   prog='analyzer.py',
                                   version='0.1b',
                                   usage='%prog [directory]')
    params.add_option("-r", "--rename",
                     action="store_true", dest="rename", default=False,
                     help="Rename the book file instead of hard linking")
    params.add_option("-e", "--extension",
                      default='epub', help='Book extension')
    params.add_option("-o", "--out",
                      default='metadata.csv', 
                      help='Metadata index file')
    params.add_option("-d", "--destination",
                      default='new', 
                      help='Directory for processed books')
    options, arguments = params.parse_args()
   
    if len(arguments) == 0:
        params.print_help()
        return 

    dest_dir = os.path.join(arguments[0], options.destination)
    _create_dest_directory(dest_dir)    
    metaWriter = csv.writer(open(options.out, 'wb'), 
                            delimiter=',', 
                            quotechar='"', 
                            quoting=csv.QUOTE_MINIMAL)

    logging.info("Starting to analyze ebooks from %s and link them in %s" % (
                                                             arguments[0],
                                                             dest_dir))
    for root, dirs, files in os.walk(arguments[0], topdown=True):
        for filename in files:
            try:
                old_filename = os.path.join(root, filename)
                new_filename = uuid.uuid4().hex + '.' + options.extension
                info = get_epub_info(old_filename)
                if options.rename:
                    os.rename(old_filename, 
                              os.path.join(arguments[0], new_filename))
                else:
                    os.link(old_filename, 
                            os.path.join(dest_dir, new_filename))
#                logging.info(info)
                metaWriter.writerow([info['creator'].encode("utf-8"),
                                     info['title'].encode("utf-8"),
                                     info['language'].encode("utf-8"),
                                     info['identifier'],
                                     new_filename,
                                     info['date'], 
                                     ])
            except Exception, excp:
                logging.error("Error while extracting metadata from %s -- %s" % 
                              (filename, excp))

def _configure_logger():
    LOG_FILENAME = os.path.join('..', 'log', 'imports.log')
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        filename=LOG_FILENAME)

def _create_dest_directory(dest_dirname):
    if not os.path.isdir(dest_dirname):
        logging.info('Creating destination directory %s.' % dest_dirname)
        os.mkdir(dest_dirname)

if __name__ == '__main__':
    main()