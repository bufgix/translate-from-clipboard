#!/usr/bin/env python2
#-*- coding: utf-8 -*-
#
#

__author__ = '@laszlokuehl'

import json, time, requests
import os, re, sys, signal, string

signal.signal(signal.SIGINT, lambda s, f: sys.exit())

PY3 = sys.version_info[0] == 3      # --
DROID = 'qpython' in sys.executable #  -- > :D
TERMUX = 'termux' in sys.executable # --

if DROID != True or TERMUX != True:
    import xerox

if PY3:
    from urllib.parse import urlencode

    if DROID:
        import sl4a
        droid = sl4a.Android()
else:
    from urllib import urlencode

    if DROID:
        import androidhelper
        droid = androidhelper.Android()

    reload(sys)
    sys.setdefaultencoding('utf-8')

class Translate(object):
    API = "http://translate.googleapis.com/translate_a/single?client=gtx&sl={from_lang}&tl={to_lang}&dt=t&{query}"

    if True in [TERMUX, DROID]:
        userpath = '/sdcard/'
    else:
        userpath = os.path.expanduser('~')

    default_config = {
        'config': os.path.join(userpath, '.sct.json'),
        'dbpath': os.path.join(userpath, '.dictorany.json'),
        'from': 'en',
        'to': 'tr'
    }

    def __init__(self, configfile=None):
        self.config = self.parse_config(configfile)
        self.database = json.loads(open(self.config['dbpath'], 'r').read())

    def invert_dict(self, d):
        return dict([(v, k) for k, v in d.items()])

    def parse_config(self, configfile=None):
        if configfile == None:
            configfile = os.path.join(self.userpath, '.sct.json')

        if os.path.exists(configfile):
            data = json.loads(open(configfile, 'r').read())
        else:
            with open(configfile, 'w') as f:
                f.write(json.dumps(self.default_config, indent=4))

            data = self.default_config

        if os.path.exists(data['dbpath']) != True:
            with open(data['dbpath'], 'w') as f:
                f.write('{}')

        return data

    def insert_db(self, from_lang, to_lang, word, translated):
        if from_lang not in self.database:
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
            from_lang=from_lang, to_lang=to_lang, query=urlencode({
                'q': word
            }))

        try:
            translated = eval(requests.get(URL).text.replace('null', 'None'))[0][0][0]
            return translated
        except:
            return None

    def translate(self, from_lang, to_lang, word):
        try:
            return self.search_db(from_lang, to_lang, word)
        except KeyError:
            translated = self.search_online(from_lang, to_lang, word)

            if word.lower() == translated.lower():
                return None

            if translated != None:
                self.insert_db(from_lang, to_lang, word, translated)

            return translated

class BaseApp(object):
    def log(self, msg):
        sys.stdout.write('[{time}] - {msg}\n'.format(time=time.ctime(), msg=msg))
        sys.stdout.flush()

    def send_notify(self, msg):
        if DROID:
            droid.makeToast(msg)

        elif TERMUX:
            pass

        else:
            command = 'notify-send -a "Translate From Clipboard" -u "Low" "{msg}"'.format(msg=msg)
            os.system(command)

    def set_clipboard(self, text=None):
        if text == None:
            text = ''

        if DROID:
            droid.setClipboard(text)
        else:
            xerox.copy(text)

    def get_clipboard(self):
        if DROID:
            return droid.getClipboard().result
        else:
            return xerox.paste()

class CliApp(BaseApp, Translate):
    def main(self):
        self.set_clipboard(text=None)

        self.log('Translate From Clipboard: Started!')
        self.log('Config: from {0} to {1}'.format(self.config['from'], self.config['to']))

        while True:
            value = self.get_clipboard()

            if value != '':
                for word in re.findall('\w+', value):
                    translated = self.translate(self.config['from'], self.config['to'], word.lower())

                    if translated != None:
                        string = '{0}: {1}'.format(*list(map(lambda x: x.capitalize(), (word, translated))))

                        self.send_notify(string)
                        self.log(string)

                    self.set_clipboard(text=None)

class TkinterApp(BaseApp, Translate):
    pass

if __name__ == '__main__':
    app = CliApp()
    app.main()
