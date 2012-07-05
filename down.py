#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey #the best thing to do is put this import in manage.py
monkey.patch_socket()

import logging
import requests
import tablib
import zlib
import re
import sys
from collections import namedtuple
import htmlentitydefs
from BeautifulSoup import BeautifulSoup, NavigableString
from redis import Redis
from urlparse import urlparse, parse_qs

import gevent
from gevent.queue import JoinableQueue, Queue

logging.basicConfig(level=logging.WARNING)

Project = namedtuple('Project', ['theme', 'activities', 'acronym',
                                 'start_date', 'end_date',
                                 'cost', 'funding',
                                 'status', 'contract_type',
                                 'coordinator', 'partners',
                                 'contact_person', 'reference', 'record'])

NUM_THEME_WORKER_THREADS = 4
NUM_PROJECT_WORKER_THREADS = 10
REQUESTS_CONFIG = {
    'max_retries': 9999,
}

THEME_URL = "http://cordis.europa.eu/fetch?CALLER=FP7_PROJ_EN&QM_EP_PGA_A=%(theme)s"
PROJECT_URL = "http://cordis.europa.eu/newsearch/getDoc?doctype=PROJ&xslt-template=projects/xsl/projectdet_en.xslt&rcn=%(project_id)s"

def theme_worker():
    def get_projects(doc):
        for result in doc.findAll(title=u"Project acronym"):
            a = result.a
            link = "http://cordis.europa.eu" + dict(a.attrs)['href'][2:]
            yield link

    logging.info('START THEME WORKER')
    while True:
        count = 0
        theme = q.get()
        logging.info('THEME: %s', repr(theme))

        url = THEME_URL % {'theme': theme}
        try:
            while True:
                r = requests.get(url, config=REQUESTS_CONFIG)
                if not r.ok:
                    logging.error("Request failed for url: %s", url)
                    continue
                doc = BeautifulSoup(r.content)
                for proj in get_projects(doc):
                    project_queue.put((theme, proj))
                    count += 1
                try:
                    next_ = dict(doc.find(
                            text="Next 20 projects &raquo;").parent.attrs
                        )['href'][2:]
                except AttributeError:
                    break
                url = "http://cordis.europa.eu" + next_
        except Exception, e:
            logging.error("THEME_WORKER: Error for url: %s", url)
            logging.error(e)
        finally:
            logging.info('THEME: %s finished, %d projects', repr(theme), count)
            q.task_done()


def _get_p_br_entry(doc, name):
    try:
        regex = re.compile('{0}[ ]*:?[ ]*'.format(name), re.IGNORECASE)
        text = doc.find(text=regex)

        if not text:
            return ''

        p = text.parent.nextSibling
        while p is not None and (not isinstance(p, NavigableString) or not p.strip()):
            p = p.nextSibling

        if p is None:
            p = text.parent.text

        return re.sub(regex, '', p).strip(": \t|\\/")
    except:
        logging.error("FAILED ON ``{1}'': {0}".format(doc, name))
        raise
from requests.packages.urllib3.connectionpool import *

def project_worker():
#    global project_cache
    logging.info('START PROJECT WORKER')

    re_query = re.compile("QUERY=[a-zA-Z0-9\:]+")
    max_partners = 0
    red = Redis(host="127.0.0.1", db=6)
    while True:
        url = ""
        try:
            theme, orig_url = project_queue.get()
            url = str(orig_url)
            match = re_query.search(url)
            key = url.replace( url[match.start():match.end()+1], "" )
            logging.info('PROJECT: %s: %s' % (theme, url))

            value = red.get(key)
            try:
                page = zlib.decompress(value)
            except:
                logging.warning('CACHE MISS ON {0}'.format(key))
                r = requests.get(url, config=REQUESTS_CONFIG)

                if not r.ok:
                   logging.error("Request failed for url: %s", url)
                   continue

                # in order to retrieve the actual content of the page, which
                # is loaded through ajax, we need to find the id of this
                # project and load the actual URL
                page = r.content
                doc = BeautifulSoup(page)
                try:
                    project_id = doc.find('input', attrs={'name':"REF"}).get('value')
                except AttributeError:
                    logging.error("UNABLE TO FIND ``input name=ref'' at {0} into {1}".format(url, doc))
                    # extract project_id in a least ``politically-correct'' way
                    project_id = parse_qs(urlparse(url).query)['RCN'][0]

                project_url = PROJECT_URL % {'project_id': project_id}

                r = requests.get(project_url, config=REQUESTS_CONFIG)
                page = r.content

                red.set(key, zlib.compress(page, 9))

            content = BeautifulSoup(page, convertEntities="html", smartQuotesTo="html", fromEncoding="utf-8")

            # extract useful chunks of content
            data_info = content.find(attrs={'class':'projdates'})
            data_coordinator = content.find(attrs={'class': 'projcoord'})
            data_details = content.find(attrs={'class': 'projdet'})
            data_participants = content.find(attrs={'class': 'participants'})
            data_footer = content.find(attrs={'id': 'recinfo'})

            if data_details is None:
                logging.error("You're kidding me, no details page...")
                logging.error("This page has something wrong, I'm going to remove it from the cache...")
                red.delete(key)
                raise

            # extract useful information about this project
            activities = _get_p_br_entry(data_details, "subprogramme area")
            acronym = content.find('h1').text
            if data_info:
                start_date = _get_p_br_entry(data_info, "from")
                end_date = _get_p_br_entry(data_info, "to")
            else:
                start_date = ''
                end_date = ''
            cost = convert_to_currency(_get_p_br_entry(data_details, "total cost"))
            funding = convert_to_currency(_get_p_br_entry(data_details, "EU contribution"))
            status = _get_p_br_entry(data_details, "status")
            contract_type = _get_p_br_entry(data_details, "contract type")
            coordinator = extract_institution(data_coordinator)
            contact = _get_p_br_entry(data_coordinator, "administrative contact")
            reference = _get_p_br_entry(data_details, "project reference")
            record = _get_p_br_entry(data_footer, "record number")

            partners = []
            if data_participants is not None:
                for participant in data_participants.findAll(attrs={'class': 'participant'}):
                    partners.append(extract_institution(participant))

            project = Project(theme, activities, acronym, start_date,
                              end_date, cost, funding,
                              status, contract_type, coordinator,
                              partners, contact, reference, record)

            max_partners = max(max_partners, len(partners))

            length_queue.put(len(partners))
            out_queue.put(project)
        except Exception, e:
            logging.exception(e)
            print '============', url
            sys.exit()
        finally:
            project_queue.task_done()


def get_themes():
    # http://cordis.europa.eu/fp7/projects_en.html
    r = requests.get('http://cordis.europa.eu/fp7/projects_en.html', config=REQUESTS_CONFIG)
    assert r.status_code == 200, "Error retrieving themes"
    doc = BeautifulSoup(r.content)
    for option in doc.find(id="themes"):
        try:
            option = option.string.strip()
        except:
            continue
        if not option or option == u"Any":
            continue
        yield option


def convert_to_currency(string):
    return string.replace('EUR', '').replace(' ', '')


def extract_institution(obj):
    return u"{0} - COUNTRY: {1}".format(
        obj.find('div', attrs={'class': 'name'}).text,
        obj.find('div', attrs={'class': 'country'}).text
    ).replace(u'(+)', u'')


def get_timestamp():
    """
    returns a string containg the timestamp (in seconds)
    """
    from datetime import datetime
    from time import mktime

    return str(mktime(datetime.utcnow().timetuple()))[:-2]


# Thanks to Fredrik Lundh, http://effbot.org/zone/re-sub.htm#unescape-html
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


if __name__ == "__main__":
#    project_cache = shelve.open("project_cache.shelve")

    q = JoinableQueue()
    project_queue = JoinableQueue()
    out_queue = Queue()
    length_queue = Queue()

    for i in range(NUM_THEME_WORKER_THREADS):
         gevent.spawn(theme_worker)

    for i in range(NUM_PROJECT_WORKER_THREADS):
         gevent.spawn(project_worker)

#    i = 0
    for item in get_themes():
        q.put(item)
#        i += 1
#        if i >= 1:
#            break

    try:
        q.join()  # block until all tasks are done
        project_queue.join()
    except KeyboardInterrupt:
        logging.info('CTRL-C: save before exit')
        raise

    length_queue.put(StopIteration)
    max_length = 0
    for length in length_queue:
        if max_length < length:
            max_length = length

    out_queue.put(StopIteration)
    data = None

    headers = ["Theme", "Activities (research area)", "Project Acronym", "Start Date", "End Date", "Project Cost", "Project Funding", "Project Status", "Contract Type", "Coordinator", "Project Reference", "Record"]
    for i in range(max_length):
        headers.append("Partner %d" % (i+1))
    data = tablib.Dataset(headers=headers)
    for i, out in enumerate(out_queue):
        logging.info('OUT: %d', i)
        row = [out.theme, out.activities, out.acronym, out.start_date, out.end_date, out.cost, out.funding, out.status, out.contract_type, out.coordinator, out.reference, out.record]
        for i in out.partners:
            row.append(i)
        for i in range(max_length - len(out.partners)):
            row.append("")
        data.append(row)

    with open('projects.%s.csv' % (get_timestamp(),), 'w') as f:
        f.write(data.csv)
