# -*- coding: utf-8 -*-
###
# Copyright (c) 2013, duenni
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###
import re
import urllib2
from lxml import etree
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('OFDb')

@internationalizeDocstring
class OFDb(callbacks.Plugin):
    """Add the help for "@plugin help OFDb" here
    This should describe *how* to use this plugin."""
    threaded = True

    def ofdb(self, irc, msg, args, searchterm):
        """<movie>
        output info from OFDb about a movie
        """

        search = urllib2.quote(searchterm)
        url = 'http://ofdbgw.org/search/%s'%search
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        headers = { 'User-Agent' : user_agent }

        try:
            #url = urllib2.urlopen('http://ofdbgw.org/search/%s'%search)
            req = urllib2.Request(url, '', headers)
            req.add_header('User-Agent', user_agent)
            response = urllib2.urlopen(req)
            tree = etree.parse(response)    
        except Exception, e:
            irc.reply('Ich konnte die Seite nicht öffnen %s'% e, prefixNick=False)
            return 
     
        #check ofdbgw.org return codes
        rcode = tree.xpath('//rcode/text()')
        
        #If there ae no errors, search
        if rcode[0].strip() == '0':
            elem_id = tree.xpath('//eintrag/id/text()')
            elem_title = tree.xpath('//eintrag/titel/text()')
            if elem_id:
                for i in range(len(elem_id)):
                    if re.search('^' + searchterm + '$', elem_title[i].strip(), re.IGNORECASE): 
                        ofdbid=elem_id[i].strip()
                        break
                    if re.search(searchterm, elem_title[i].strip(), re.IGNORECASE):     
                        ofdbid=elem_id[i].strip()

            #We have an ID, parse it's URL to get the details
            url = 'http://ofdbgw.org/movie/%s'%ofdbid
            try:
                req = urllib2.Request(url, '', headers)
                req.add_header('User-Agent', user_agent)
                response = urllib2.urlopen(req)
                tree = etree.parse(response)  
            except Exception, e:
                irc.reply('Ich konnte die Seite nicht öffnen: %s'% e, prefixNick=False)
                return 
            rcode = tree.xpath('//rcode/text()')

        if rcode[0].strip() == '1':
            irc.reply('Unbekannter Fehler.', prefixNick=False)
            return         
        elif rcode[0].strip() == '2':
            irc.reply('Fehler oder Timeout bei der Anfrage.', prefixNick=False)
            return
        elif rcode[0].strip() == '3':
            irc.reply('Keine oder falsche ID angegeben.', prefixNick=False)
            return
        elif rcode[0].strip() == '4':
            irc.reply('Keine Daten zu angegebener ID oder Query gefunden.', prefixNick=False)
            return
        elif rcode[0].strip() == '5':
            irc.reply('Fehler bei der Datenverarbeitung.', prefixNick=False)
            return
        elif rcode[0].strip() == '9':
            irc.reply('Wartungsmodus, OFDBGW derzeit nicht verfügbar.', prefixNick=False) 
            return          

        #Deutscher Titel
        elem = tree.xpath('//resultat/titel/text()')
        if elem:
            title = elem[0].strip()
            titlelink = title.replace(' ','-')
        else:
            title = '-'
            titlelink = '-'  

        #Originaltitel
        elem = tree.xpath('//alternativ/text()')
        if elem:
            titleorig = elem[0].strip()
        else:
            titleorig = ''
        
        #Jahr
        elem = tree.xpath('//jahr/text()')
        if elem:
            year = elem[0].strip()
        else:
            year = ''              
        
        #Kurzbeschreibung
        elem = tree.xpath('//kurzbeschreibung/text()')
        if elem:
            descr = re.sub("^ *\(Quelle.*?\)","",elem[0].strip()) #Regex for stripping (Quelle: Covertext » eigenen Text einstellen)
        else:
            descr = ''    

        #Regie
        elem = tree.xpath('//regie/person/name/text()')
        if elem:
            regie = elem[0].strip()
        else:
            regie = '' 

        #Bewertung
        elem = tree.xpath('//bewertung/note/text()')
        if elem:
            bewertung = elem[0].strip()
        else:
            bewertung = ''  

        #Fassungen
        elem = tree.xpath("count(//fassungen/titel/land[text()='Deutschland'])")
        if elem:
            fassungger = int(elem)
        else:
            fassungger = 0  

        elem = tree.xpath("count(//fassungen/titel)")
        if elem:
            fassungall = int(elem)
        else:
            fassungall = 0 

        #Genres
        elem = tree.xpath('//genre/titel/text()')
        if elem:
            genre = '/'.join(elem)
        else:
            genre = '-'        

        #Reply
        irc.reply(ircutils.bold(ircutils.mircColor('OFDb', fg='yellow', bg='red')+' http://www.ofdb.de/film'+'/'+ofdbid+','+titlelink), prefixNick=False)
        irc.reply(ircutils.bold('Title: ')+title+' ('+year+')'+' '+bewertung+'/10', prefixNick=False)
        irc.reply(ircutils.bold('Originaltitel: ')+titleorig, prefixNick=False)
        irc.reply(ircutils.bold('Inhalt: ')+descr+' (...)', prefixNick=False)   
        irc.reply(ircutils.bold('Regie: ')+regie+ircutils.bold(' Genres: ')+genre, prefixNick=False)
        irc.reply(ircutils.bold('Eingetragene Fassungen:')+' Deutschland %s / Rest der Welt %s'%(fassungger,(fassungall - fassungger)), prefixNick=False)        

    ofdb = wrap(ofdb, ['text'])
Class = OFDb


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
