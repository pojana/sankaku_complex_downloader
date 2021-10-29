# from os import write
# from posix import uname_result
# from scrape_sankakucomplex.complex import save_img
import requests
# from bs4 import BeautifulSoup
# import urllib
import csv
import re

from concurrent.futures import ThreadPoolExecutor
import pathlib
import time
import datetime

import sys
import os

import pprint
import json
from collections import OrderedDict

# from requests.sessions import RecentlyUsedContainer

# from requests.models import Response

USER = ''
PASS = ''

src_save_path = ''

WORKERS = 30


class sankaku():
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.headers = {}
        self.limit = WORKERS
     
    def login(self):
        url = "https://capi-v2.sankakucomplex.com/auth/token"
        headers = {"Accept": "application/vnd.sankaku.api+json;v=2"}
        headers["User-Agent"] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0"
        data = {"login": self.username, "password": self.password}

        response = requests.post(url=url, headers=headers, json=data)
    
        print(response)
        data = response.json()

        if response.status_code >= 400 or not data.get("success"):
            print('login error')
        return "Bearer " + data["access_token"]

    def authenticate(self):
        self.headers = {"Accept": "application/vnd.sankaku.api+json;v=2"}
        self.headers["User-Agent"] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0"
        self.headers["Authorization"] = self.login()

        print(self.headers)

    def posts_one(self, post_id):
        params = {
            "lang" : "en",
            "page" : "1",
            "limit": "1",
            "tags" : "id_range:" + post_id,
        }

        # self.authenticate()

        return self.call("/posts", params)

    def posts_tag(self, tags):
        params = {'tags': tags.replace("+", " ")}

        # self.authenticate()

        return self.pagination("/posts/keyset", params)

    def posts_books(self, tag):
        params = {"tags": tag, "pool_type": "0"}
        
        for pools in self.pagination("/pools/keyset", params):
            for pool in pools:
                # url = "https://sankaku.app/books/{}".format(pool["id"])
                
                # print(pool)
                book_name = pool['name_en'] \
                    if pool['name_ja'] is None else pool['name_ja']
                # print('name: {}, posts: {}\nfile_url: {}'.format(
                #     pool['name'], pool['id'], pool['file_url']))

                data = self.pools(str(pool['id']))
                
                yield book_name, pool['id'], data['posts']

    def pools(self, pool_id):
        params = {"lang": "en"}
        return self.call("/pools/" + pool_id, params)

    def pagination(self, endpoint, params):
    
        params["lang"] = "en"
        params["limit"] = str(self.limit)

        count = 0

        while True:
            data = self.call(endpoint, params)
 
            if data is None:
                print('None data')
                data = self.call(endpoint, params)
            else:
                pass

            try:
                yield data["data"]
            except KeyError:
                print(data)
                print(count)
                return

            count += len(data["data"])

            params["next"] = data["meta"]["next"]
            if not params["next"]:
                print(count)
                return

    def call(self, endpoint, params=None):
        url = "https://capi-v2.sankakucomplex.com" + endpoint
        # self.authenticate()

        # response = requests.get(url=url, params=params, headers=self.headers)
        # print(response)

        for _ in range(5):
            self.authenticate()
            response = requests.get(
                url, params=params, headers=self.headers)

            if response.status_code == 200:
                break

            if response.status_code == 429:
                until = response.headers.get("X-RateLimit-Reset")
                for i in until:
                    print("{}/{}".format(i, until))
                    time.sleep(1)
                continue

        data = response.json()

        try:
            success = data.get("success", True)
        except AttributeError:
            success = True
    
        return data


class extract_text():
    def __init__(self):
        self.max_workers = WORKERS
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0"
        }
        self.filter = []
        self.tag = ''
        self.book_name = ''
        self.save_dir = './'

    def set_save_path(self, txt_name):
        self.save_dir = src_save_path + txt_name + '\\'
        print(self.save_dir)

    def get_all_posts(self, tag):
        check = check_post()
        self.tag = tag

        self.filter = check.check_posts(tag, self.save_dir)
        print('aleady download posts: {}'.format(len(self.filter)))

        self.get_books_tag(tag)
        self.get_posts_tag(tag)

    def get_posts_tag(self, tag):
        san = sankaku(USER, PASS)
        self.tag = tag
        self.book_name = ''
        # file_count = 1

        for d in san.posts_tag(tag):
            data_list_all = []
            for x in d:
                
                if [s for s in self.filter if x['id'] == s]:
                    print('aleady download : {}'.format(x['id']))
                    continue
                
                file = self.select_file(x, file_count=0)

                # file_count += 1
                if file[1]:
                    data_list_all.append(file)
                else:
                    self.save_log(file, errorflag=True)
                
            save_path = self.save_dir + \
                re.sub(r'[\\|/|:|?|.|!|*|"|<|>|\|]', '_', tag)

            pathlib.Path(save_path).mkdir(exist_ok=True)
            
            # self.insert_csv(data_list_all, tag)
            self.save_image_multithread(data_list_all, save_path=save_path)
            # pprint.pprint(data_list_all, width=300)

    def get_books_tag(self, tag):
        san = sankaku(USER, PASS)
        self.tag = tag

        save_path = self.save_dir + \
            re.sub(r'[\\|/|:|?|.|!|*|"|<|>|\|]', '_', tag) + '\\'

        pathlib.Path(save_path).mkdir(exist_ok=True)

        # save_path += 'books\\'
        
        # pathlib.Path(save_path).mkdir(exist_ok=True)

        # count = 0
        for book_id, book_name, book_posts in san.posts_books(tag):
            
            self.book_name = book_name
            book_dl_list = []
            for i, post in enumerate(book_posts):
                
                if [s for s in self.filter if post['id'] == s]:
                    print('aleady download : {}'.format(post['id']))
                    continue

                i += 1
                dl = self.select_file(post, i)
                
                if dl[1]:
                    book_dl_list.append(dl)

                    self.filter.append(post['id'])
                else:
                    
                    self.save_log(dl, errorflag=True)
                    
            print('book_id: {}, book_name: {}'.format(book_id, book_name))
            # pprint.pprint(book_dl_list, width=300)
 
            book_dir = '{}, {}'.format(book_id, book_name)
            book_path = save_path + \
                re.sub(r'[\\|/|:|?|.|!|*|"|<|>|\|]', '_', book_dir) + '\\'
            
            pathlib.Path(book_path).mkdir(exist_ok=True)

            self.save_image_multithread(book_dl_list, save_path=book_path)

    def get_post_one(self, post_id):
        san = sankaku(USER, PASS)

        data = san.posts_one(post_id=post_id)[0]
        print(data)

        data = self.select_file(data, 0)
        self.save_image(data)

    def select_file(self, data, file_count):

        # file_name -> '1_post :id, :tag.jpg'

        if data['tags'] == []:
            tag = 'None'
        elif data["tags"][0]["name_ja"] is None:
            tag = data["tags"][0]["name_en"]
        else:
            tag = data["tags"][0]["name_ja"]

        if file_count == 0:
            file_name = '{}, {}'.format(data['id'], tag)
        else:
            file_name = '{}_post {}, {}'.format(
                file_count, data['id'], tag)
        
        if data['file_url'] is None:
            if data["sample_url"] is None:
                file_url = None
                file_name = re.sub(r'[\\|/|:|?|.|!|*|"|<|>|\|]', '-', file_name)
                return [file_name, file_url]
            else:
                extension = self.select_extension(data["sample_url"])
                file_url = data["sample_url"]
        else:
            extension = self.select_extension(data["file_url"])
            file_url = data["file_url"]

        file_name = re.sub(r'[\\|/|:|?|.|!|*|"|<|>|\|]', '-', file_name)
        file_name += extension

        dl = [file_name, file_url]

        # print("fileName: {}, url: {}".format(dl[0], dl[1]))
        return dl

    def select_extension(self, url):
        extension_list = ['.jpg', '.gif', '.mp4', '.webm', '.png']
        for ext in extension_list:
            if ext in url:
                return ext
        
        return '.jpg'

    def insert_csv(self, data_list, csv_name):
        # csv_name = urllib.parse.unquote(csv_name)
        csv_name = re.sub(r'[\\|/|:|?|.|"|!|*|<|>|\|]', '-', csv_name)
        csv_name += '.csv'

        with open('./ready\\' + csv_name, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file,
                                quoting=csv.QUOTE_ALL,
                                delimiter=',')
            
            writer.writerows(data_list)

    def save_image_multithread(self, data_list, save_path):

        for data in data_list:
            extension = self.select_extension(data[1])
            extension = extension.replace('.', '')

            # if 'jpg' in extension or 'png' in extension:
            if 'jpg' in extension or 'png' in extension:
                data[0] = save_path + '\\' + data[0]
            else:
                ext_path = save_path + '\\　' + extension
                
                pathlib.Path(ext_path).mkdir(exist_ok=True)
                data[0] = ext_path + '\\' + data[0]

            ## ここにタイムスタンプのやつを追加していく

        # pprint.pprint(data_list, width=300)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            executor.map(self.save_image, data_list)

    def save_image(self, data):
        img = requests.get(data[1], headers=self.headers)

        if img.status_code == 200:
            print('response: {}, filename: {}, \nurl: {}'.format(
                str(img.status_code), data[0], data[1]
            ))

            with open(data[0], 'wb') as file:
                file.write(img.content)
            
            self.save_log(data, False)

        else:
            print('!Failed! response: {}, filename: {}, \nurl: {}'.format(
                str(img.status_code), data[0], data[1]
            ))
            self.save_log(data, True)

    def save_log(self, data, errorflag):
        # log_name = re.sub(r'mp4|gif|webm|png|.jpg', '', log_name)

        # print(log_name)

        # log_name = log_name.split('\\')[0]

        def_dir = './log_error\\' if errorflag else './log\\'

        if not self.tag:
            log_name = def_dir + data[0]
        else:
            log_name = def_dir + str(self.tag)
            pathlib.Path(log_name).mkdir(exist_ok=True)
            
            if self.book_name:
                log_name = log_name + '\\' + str(self.book_name)
                pathlib.Path(log_name).mkdir(exist_ok=True)
            else:
                pass

        with open(log_name + '.log', 'a') as logfile:
            if not data[1]:
                data[1] = 'None'
            else:
                pass
            logfile.write(','.join(data) + '\n')


class check_post():
    def __init__(self):
        pass
    
    def check_posts_home(self, check_dir):
        # .jpg, .png の post id を取り出す
        # '78_posts ' が入ってることを意識して

        posts_list = []
        file_list = list(pathlib.Path(check_dir).glob('*.*'))

        for f in file_list:

            tag = str(f.name).split(',')
            tag[0] = re.sub('[0-9]*_post ', '', tag[0])

            try:
                append_tag = int(tag[0])
                posts_list.append(append_tag)
            except ValueError:
                print(tag[0])
                
        # print(posts_list)
        return posts_list

    def check_posts_sub(self, check_dir):
        # print(check_dir)
        files = os.listdir(check_dir)
        sub_list = [f for f in files if os.path.isdir(os.path.join(check_dir, f))]
        
        # print(len(sub_dir))

        posts_list = []
        if len(sub_list) != 0:
            for sub in sub_list:
                sub_dir = check_dir + '\\' + sub

                sub_res = self.check_posts_sub(sub_dir)
                posts_list.extend(sub_res)

                res = self.check_posts_home(check_dir + '\\' + sub)
                posts_list.extend(res)

        # print(posts_list)
        # print(len(posts_list))

        return posts_list

    def check_posts(self, tag, check_dir):
        posts_list = []

        save_path = check_dir + \
            re.sub(r'[\\|/|:|?|.|!|*|"|<|>|\|]', '_', tag) + '\\'

        if os.path.exists(save_path):

            posts_list.extend(self.check_posts_home(save_path))

            posts_list.extend(self.check_posts_sub(save_path))
        else:
            pass

        return posts_list


def save_tag_text(tag_list, src_path):

    end_path = src_path.replace('.txt', '') + '_end.txt'
    with open(end_path, mode='a', encoding='utf-8') as f:
        t = tag_list[0] + '\n'
        f.write(t)

    tag_list.pop(0)

    with open(src_path, mode='w', encoding='utf-8') as f:
        for i in tag_list:
            t = i + '\n'
            f.write(t)


def main():
    extractor = extract_text()

    args = sys.argv

    if len(args) >= 2:
        if '.txt' in args[1]:
            print('get multiple')

            with open(args[1], mode='r', encoding='utf-8') as file:
                tag_list = file.readlines()
                tag_list = [li.rstrip() for li in tag_list]

            text_name = args[1].split('\\')[-1].replace('.txt', '')
            extractor.set_save_path(txt_name=text_name)

            while True:
                if tag_list == []:
                    print("all tags scrape!")
                    return
                
                if tag_list[0] == '':
                    print('skip null tag')
                    tag_list.pop(0)
                    continue

                print(tag_list[0])

                t1 = time.time()

                extractor.get_all_posts(tag=tag_list[0])

                extractor.get_books_tag(tag=tag_list[0])

                t2 = time.time()
                session_times = t2 - t1
                print('実行時間: {}'.format(
                    datetime.timedelta(seconds=session_times)))

                save_tag_text(tag_list=tag_list, src_path=args[1])
        
        elif 'tag:' in args[1]:
            print('get items from tag')
            tag = args[1].replace('tag:')
            extractor.get_all_posts(tag)

        else:
            print('get one post')
            post_id = args[1]
            extractor.get_post_one(post_id)
    else:
        pass


if __name__ == '__main__':
    main()
