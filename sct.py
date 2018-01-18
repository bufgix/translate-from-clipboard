#!/usr/bin/env python2
#-*- coding: utf-8 -*-
#
#

__author__ = '@laszlokuehl'

import os, sys, signal, xerox
import json, requests, string

signal.signal(signal.SIGINT, lambda s, f: sys.exit())

if sys.version_info[0] == 2:
    from urllib import urlencode

    reload(sys)
    sys.setdefaultencoding('utf-8')
    letters = string.letters
else:
    from urllib.parse import urlencode
    letters = string.ascii_letters

letters += 'üÜıİöÖşŞğĞçÇ'

default_config = {
    'config': '{}/.sct.json'.format(os.path.expanduser('~')),
    'dbpath': '{}/.dictorany.json'.format(os.path.expanduser('~')),
    'from': 'en',
    'to': 'tr'
}

class Translate(object):
    def __init__(self, configfile=None):
        self.API = "http://translate.googleapis.com/translate_a/single?client=gtx&sl={from_lang}&tl={to_lang}&dt=t&{query}"

        self.userpath = os.path.expanduser('~')
        self.config = self.parse_config(configfile)

        self.database = json.loads(open(self.config['dbpath'], 'r').read())

    def invert_dict(self, d):
        return dict([(v, k) for k, v in d.items()])

    def get_word(self, string):
        return ''.join([x for x in string if x in letters])

    def parse_config(self, configfile=None):
        if configfile == None:
            configfile = os.path.join(self.userpath, '.sct.json')

        if os.path.exists(configfile):
            data = json.loads(open(configfile, 'r').read())
        else:
            with open(configfile, 'w') as f:
                f.write(json.dumps(default_config, indent=4))

            data = default_config

        if os.path.exists(data['dbpath']) != True:
            with open(data['dbpath'], 'w') as f:
                f.write('{}')

        return data

    def send_notify(self, msg):
        command = 'notify-send -a "STC" -u "Low" "{msg}"'.format(msg=msg)
        os.system(command)

    def insert_db(self, from_lang, to_lang, word, translated):
        if from_lang not in self.database.keys():
            self.database[from_lang] = {}

        if word not in self.database[from_lang].keys():
            self.database[from_lang][word.lower()] = {}

        self.database[from_lang][word.lower()][to_lang] = translated

        with open(self.config['dbpath'], 'w') as f:
            f.write(json.dumps(self.database, indent=4))

    def search_db(self, from_lang, to_lang, word):
        return self.database[from_lang][word][to_lang]

    def search_online(self, from_lang, to_lang, word):
        URL = self.API.format(
            from_lang=from_lang,
            to_lang=to_lang,
            query=urlencode({
                'q': word
            }))
        translated = eval(requests.get(URL).text.replace('null', 'None'))[0][0][0]

        return translated

    def translate(self, from_lang, to_lang, word):
        try:
            return self.search_db(from_lang, to_lang, word)
        except KeyError:
            translated = self.search_online(from_lang, to_lang, word)

            if translated != None:
                self.insert_db(from_lang, to_lang, word, translated)

            return translated

class CliApp(Translate):
    """
    Cli app for Translate class
    """
    def main(self):
        xerox.copy('')

        while True:
            if xerox.paste() != '':
                word = xerox.paste()

                for word in word.split(' '):
                    word = self.get_word(word)

                    translated = self.translate(self.config['from'], self.config['to'], word)
                    self.send_notify('* {0}: {1}'.format(word, translated))

                    xerox.copy('')

if __name__ == '__main__':
    app = CliApp()
    app.main()
