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

        try:
            url = urllib2.urlopen('http://ofdbgw.org/search/%s'%search)
            tree = etree.parse(url)
        except:
            irc.reply('Ich konnte die Seite nicht öffnen')
            return       
        
        #check ofdbgw.org return codes
        rcode = tree.xpath('//rcode/text()')
        
        if rcode[0].strip() == '0':
            elem = tree.xpath('//eintrag/id/text()')
            if elem:
                ofdbid = elem[0].strip()
            else:
                ofdbid = ''

            try:
                url = urllib2.urlopen('http://ofdbgw.org/movie/%s'%ofdbid)
                tree = etree.parse(url)
            except:
                irc.reply('Ich konnte die Seite nicht öffnen')
                return                 
            rcode = tree.xpath('//rcode/text()')

        if rcode[0].strip() == '1':
            irc.reply('Unbekannter Fehler.')
            return         
        elif rcode[0].strip() == '2':
            irc.reply('Fehler oder Timeout bei der Anfrage.')
            return
        elif rcode[0].strip() == '3':
            irc.reply('Keine oder falsche ID angegeben.')
            return
        elif rcode[0].strip() == '4':
            irc.reply('Keine Daten zu angegebener ID oder Query gefunden.')
            return
        elif rcode[0].strip() == '5':
            irc.reply('Fehler bei der Datenverarbeitung.')
            return
        elif rcode[0].strip() == '9':
            irc.reply('Wartungsmodus, OFDBGW derzeit nicht verfügbar.') 
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
            descr = elem[0].strip()
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

        #Reply
        irc.reply(ircutils.bold(ircutils.mircColor('OFDb', fg='yellow', bg='red')+' http://www.ofdb.de/film'+'/'+ofdbid+','+titlelink))
        irc.reply(ircutils.bold('Title: ')+title+' ('+year+')'+' '+bewertung+'/10')
        irc.reply(ircutils.bold('Originaltitel: ')+titleorig)
        irc.reply(ircutils.bold('Inhalt: ')+descr)   
        irc.reply(ircutils.bold('Regie: ')+regie)

    ofdb = wrap(ofdb, ['text'])
Class = OFDb


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
