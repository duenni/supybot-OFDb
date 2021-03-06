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
		#ofdbgw.org redirects to one of this mirrors, some of them time out a lot (response code = 2), so we ask every mirrorsite instead of using the loadbalancer. Thats not that nice but if using ofdbgw.org alone >80% of the users queries will time out.
		servers = ['http://ofdbgw.scheeper.de', 
		'http://ofdbgw.home-of-root.de', 
		'http://ofdbgw.metawave.ch', 
		'http://ofdbgw.h1915283.stratoserver.net', 
		'http://ofdbgw.johann-scharl.de', 
		'http://ofdbgw.geeksphere.de']

		#For building the final URL
		moviesearch = '/search/'
		detailsearch = '/movie/'	
		search = urllib2.quote(searchterm)

		for server in servers:
			url = server+moviesearch+search
			try:
				response = urllib2.urlopen(url)
				tree = etree.parse(response)
				rcode = tree.xpath('//rcode/text()')#response code from ofdbgw, 0 means "no errors"
				if rcode[0].strip() == '0' or rcode[0].strip() == '4': #break if no error or no movie found
					break    
			except Exception, e:
				rcode = ['-']
				continue

		#If there are no errors, search for appropriate ID
		if rcode[0].strip() == '0':
			elem_id = tree.xpath('//eintrag/id/text()')
			elem_title = tree.xpath('//eintrag/titel/text()')
			if elem_id:
				for i in range (len(elem_id)):
					if re.search('^' + searchterm + '$', elem_title[i].strip(), re.IGNORECASE): 
						ofdbid = elem_id[i].strip()
						break
					elif re.search(searchterm, elem_title[i].strip(), re.IGNORECASE):     
						ofdbid = elem_id[i].strip()
					else:
						ofdbid = elem_id[0].strip()
			#We have an ID, parse it's URL to get the details                
			for server in servers:
				url = server+detailsearch+ofdbid
				try:
					response = urllib2.urlopen(url)
					tree = etree.parse(response)
					rcode = tree.xpath('//rcode/text()')
					if rcode[0].strip() == '0':
						break    
				except Exception, e:
					continue 

		if rcode[0].strip() == '1':
			irc.reply('Unbekannter Fehler.', prefixNick=False)
			return         
		elif rcode[0].strip() == '2':
			irc.reply('Fehler oder Timeout bei der Anfrage von Gateway zu OFDb.', prefixNick=False)
			return
		elif rcode[0].strip() == '3':
			irc.reply('Keine oder falsche ID angegeben.', prefixNick=False)
			return
		elif rcode[0].strip() == '4':
			irc.reply('Kein passender Film gefunden.', prefixNick=False)
			return
		elif rcode[0].strip() == '5':
			irc.reply('Fehler bei der Datenverarbeitung.', prefixNick=False)
			return
		elif rcode[0].strip() == '9':
			irc.reply('Wartungsmodus, OFDBGW derzeit nicht verfügbar.', prefixNick=False) 
			return
		#if rcode has no value and 'e' exists -> seems like no gatewayserver could be reached, reply with exception from for-loop
		elif 'e' in locals() and rcode[0].strip() == '-': 
			irc.reply('Kein Gateway erreichbar: %s'% e, prefixNick=False)
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
