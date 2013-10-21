#coding=gbk
'''
    my[at]lijiejie.com    http://www.lijiejie.com
    login box.net and fetch all file share links
'''

import urllib2, urllib
import re
import cookielib
import httplib
import sys
import json


class Crawler:
    #override http_error_302 method
    class HttpRedirect_Handler(urllib2.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
            pass
        
    def __init__(self, email, passwd):
        self.email = email
        self.passwd = passwd
        self.headers = {
           'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:24.0) Gecko/20100101 Firefox/24.0',
           'Origin': 'https://app.box.com',
           'Referer': 'https://app.box.com/login',
        }
        # to enable http debug, add 2 more hanlders below to urllib2.build_opener()
        # httpHandler = urllib2.HTTPHandler(debuglevel=1)
        # httpsHandler = urllib2.HTTPSHandler(debuglevel=1)
        self.cookie = cookielib.CookieJar()
        self.opener = urllib2.build_opener(self.HttpRedirect_Handler(),
                                           urllib2.HTTPCookieProcessor(self.cookie))
        urllib2.install_opener(self.opener)    #global opener
        self.gen_token()

    #generate request token and cookie
    def gen_token(self):
        try:
            req = urllib2.Request('https://app.box.com/login', headers=self.headers)
            html_doc = self.opener.open(req).read()
            self.request_token = re.search("request_token = '(.*?)'", html_doc).group(1)
        except Exception,e:
            print 'fail to get request token or cookie:', e    
            sys.exit(1)
    
    def login(self):
        print 'try user login:', self.email
        params = urllib.urlencode({'login': self.email, 'password': self.passwd,
                                   '_pw_sql':'', 'reg_step':'', 'folder':'',
                                   '__login': 1, 'submit1': 1,
                                   'remember_login': 'on',
                                   'login_or_register_mode': 'login',
                                   'request_token': self.request_token})
        try:
            req = urllib2.Request('https://app.box.com/login', params, self.headers)
            self.opener.open(req)
        except Exception, e:    #response 302 will raise an http error
            if unicode(e) == 'HTTP Error 302: Found':
                print 'user logged in.'
            else:
                raise Exception('!!! falil to login')
            
    def ls(self, folder, sorted_by='date', sorted_direction='DESC'):
        html_doc = urllib2.urlopen('https://app.box.com/').read()
        m_folder = re.search('id="filename_(\d+)" name="' + folder + '"><a href="/files/0/f/(\d+)/' + folder + '"', html_doc)
        if m_folder is None:
            raise Exception('can not find your selected folder')
        folder_id = m_folder.group(1)

        #enter selected directory, get new token id and realtime_subscriber_id
        print 'enter direcotry:', folder
        html_doc = urllib2.urlopen('https://app.box.com/files/0/f/' + folder_id + '/' + folder).read()
        self.request_token = re.search("request_token = '(.*?)'", html_doc).group(1)
        self.realtime_subscriber_id = re.search("realtime_subscriber_id ='(.*?)'", html_doc).group(1)

        page = 0
        lst_files = []
        while True:
            #list items on page $page, pagesize=20
            json_doc = urllib2.urlopen('https://app.box.com/index.php?rm=box_item_list&q[sort]=' + sorted_by +
                                       '&q[direction]=' + sorted_direction + '&q[id]=d_' + folder_id +
                                       '&q[page_num]=' + str(page) + '&q[page_size]=20&q[theme_id]=1&q[collection_id]=0').read()
            o_json = json.loads(json_doc)
            file_not_found = True    #no files found on page $page
            for db_item in o_json['db'].items():
                if db_item[0].startswith('file_'):
                    file_not_found = False    #file found
                    file_id = db_item[0].lstrip('file_')
                    json_doc = urllib2.urlopen('https://app.box.com/index.php?rm=box_files_get_shared_info&typed_id=f_' + file_id).read()
                    shared_link = json.loads(json_doc)['db'].items()[0][1]['shared_link']
                    direct_shared_link = json.loads(json_doc)['db'].items()[0][1]['direct_shared_link']
                    if shared_link == None:    #if the file was not shared before, then share it
                        params = {'item_typed_ids[]': ('f_' + file_id),
                                  'request_token': self.request_token,
                                  'realtime_subscriber_id': self.realtime_subscriber_id,
                                  }
                        req = urllib2.Request('https://app.box.com/index.php?rm=box_share_item',
                                              urllib.urlencode(params),
                                              {})
                        json_doc = self.opener.open(req).read()
                        ret_values = json.loads(json_doc).values()
                        shared_link = ret_values[0]['shared_link']
                        direct_shared_link = ret_values[0]['direct_shared_link']
                    file_name = db_item[1]['name']
                    lst_files.append((file_name, shared_link))
                    print file_name.encode('gbk', 'ignore'), shared_link
            if file_not_found:
                return lst_files
            page += 1    #next page




