# -*- coding: utf-8 -*-
import logging
import time
import re
import locale
import codecs

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

#locale.setlocale(locale.LC_ALL,'pl_PL.UTF-8')

class SimplestTokenizer(object):
	def __call__(self,text):
		return self.split(text)
	def split(self,text):
		return text.split()
	def desplit(self,list):
			return u' '.join(list)
#end of space-to-space tokenizer

class PunctuationTokenizer(SimplestTokenizer):
	punctuation=[]
	def __init__(self):
		if len(self.punctuation)==0:
			f=open('dictionaries/punctuation.txt')
			for l in f:
				if l.startswith('#'): continue
				if len(l.strip())==0: continue
				l=l.replace('\,',",")
				self.punctuation.append(l.strip())
		pass

	def split(self,text):
		l=text.split()
		i=0
		while i < len(l):
			word=l[i]
			if word in self.punctuation:
				i+=1
				continue
			while len(word) and word[-1] in self.punctuation:#punctuation at the end of the word
				del l[i]
				l.insert(i,word[:-1])
				l.insert(i+1,word[-1])
				word=word[:-1]
			while len(word)>1 and word[0] in self.punctuation:#punctuation at the beginning of the word
				del l[i]
				l.insert(i,word[0])
				l.insert(i+1,word[1:])
				word=word[1:]
			dl = len(word)
			j=0
			while j < dl:#punctuation inside word
				if word[j] in self.punctuation:
					del l[i]
					l.insert(i,word[:j])
					l.insert(i+1,word[j])
					l.insert(i+2,word[j+1:])
					word=word[j+1:]
					dl=len(word)
					j=0
					i+=2
				j+=1
			i+=1
		return l
#end of space-to-space+punctuation tokenizer

class Slownik(object):
	def beforeProcess(self):
		pass

	def afterProcess(self):
		pass

	def metaProcess(self,list):
		self.beforeProcess()
		ret=self.process(list)
		self.afterProcess()
		return ret

	def __init__(self):
		self.tokenizer=SimplestTokenizer()

	def textInListOut(self,text):
		lin=self.tokenizer(text)
		return self.metaProcess(lin)

	def textInTextOut(self,text):
		out=self.textInListOut(text)
		return self.tokenizer.desplit(out)

	def listInListOut(self,list):
		return self.metaProcess(list)

	def listInTextOut(self,list):
		out=self.metaProcess(list)
		return self.tokenizer.desplit(out)

	def tilo(self,text):
		return self.textInListOut(text)
	def tito(self,text):
		return self.textInTextOut(text)
	def lilo(self,list):
		return self.listInListOut(list)
	def lito(self,list):
		return self.listInTextOut(list)

	def processToken(self,token):
	#generic no-op Slownik - does nothing
		raise TypeError('Abstract method `' + self._class.__name__  + '.' + self._function + '\' called')

	def process(self,list):
		for i in range(len(list)):
			token=list[i]
			ret=self.processToken(token)
			if ret!=None and ret!=token:
				list[i]=ret
		return list
#end base class Slownik

class NullSlownik(Slownik):
	def processToken(self,token):
	#generic no-op Slownik - does nothing
		return token+"+0"
#end no-op dummy Slownik implementation class

class TextFileListSlownik(Slownik):

	def __init__(self,fname,usefirst=True):
		self.pluppermap={u'Ą':u'ą',u'Ć':u'ć',u'Ę':u'ę',u'Ł':u'ł',u'Ń':u'ń',u'Ó':u'ó',u'Ś':u'ś',u'Ż':u'ż',u'Ź':u'ź'}
		self.pllowermap={}
		for k in self.pluppermap:
			self.pllowermap[self.pluppermap[k]]=k
		self.plmap={u'Ą':u'A',u'Ć':u'C',u'Ę':u'E',u'Ł':u'L',u'Ń':u'N',u'Ó':u'O',u'Ś':u'S',u'Ż':u'Z',u'Ź':u'Z',
					u'ą':u'a',u'ć':u'c',u'ę':u'e',u'ł':u'l',u'ń':u'n',u'ó':u'o',u'ś':u's',u'ż':u'z',u'ź':u'z'}
		self.tokenizer=PunctuationTokenizer()
		self.forms={}
		self.fname=fname
		self.name=fname.rpartition(".")[0].rpartition('/')[2]
		logger.debug("Loading data from "+fname+".")
		start = time.time()
		f=codecs.open(fname, mode='r', encoding='utf-8',errors='ignore',buffering=1)
		#f=open(fname)
		lists=[]
		for l in f:
			if l.startswith('#'): continue
			if len(l.strip())==0: continue
			l=l.replace('\\,',"#")
			t=l.split(',')
			for i in range(len(t)):
				t[i]=t[i].replace("#",",")
			t = [ x.strip() for x in t if x.strip()!="#" and x.strip()!="##" and len(x.strip())>0]
			lists.append(t)
		lists.reverse()# simple disambiguation -> first form that occurs
		for l in lists:
			bform=l[0]
			if usefirst: self.forms[bform]=bform
			for s in l[1:]:
				self.forms[s]=bform
		elapsed = (time.time() - start)
		logger.debug("Data loaded in "+str(elapsed)+" sec.")

	def lowerLocale(self,token):
		return ''.join(map( lambda t: self.pluppermap.get(t,t), token))

	def polonica(self,token):
		return ''.join(map( lambda t: self.plmap.get(t,t), token))

	def firstBig(self,token):
		if len(token)==0: return token
		l=list(token)
		l[0]=l[0].upper()
		if l[0] in self.pllowermap:
			l[0]=self.pllowermap[l[0]]
		return ''.join(l)


	def processToken(self,token):
		token=token.strip()
		fctrs=[ lambda x: x , lambda x: x.lower() , lambda x : self.lowerLocale(x) , lambda x : self.polonica(x) , lambda x : self.polonica(x).lower() , lambda x : self.firstBig(x) ]
		for f in fctrs:
			if f(token) in self.forms:
				return self.forms[f(token)]+"+"+self.name
		return token

#		if token in self.forms or token.lower() in self.forms or self.lowerLocale(token) in self.forms:
#			if token.lower() in self.forms and token not in self.forms:
#				token=token.lower()
#			elif self.lowerLocale(token) in self.forms and token not in self.forms:
#				token=self.lowerLocale(token)
#			return self.forms[token]+"+"+self.name
#		else:
#			return token

	def beforeProcess(self):
		pass

	def afterProcess(self):
		pass

	def unrecognized(self):
		pass

class AbbreviationSlownik(TextFileListSlownik):
	def __init__(self,fname):
		TextFileListSlownik.__init__(self,fname,False)
		self.tokenizer=SimplestTokenizer()

class RegexSlownik(TextFileListSlownik):
	def __init__(self,fname):
		TextFileListSlownik.__init__(self,fname)
		self.regexy={}
		for i in self.forms:
			self.regexy[re.compile(i)]=self.forms[i]

	def processToken(self,token):
		if token.find('+')>0: return token
		ret=""
		for s in self.regexy:
			if s.match(token):
				return self.regexy[s]+"+"+self.name
		else:
			return token

class ContinousTextRegexSlownik(RegexSlownik):
	def __init__(self,fname):
		RegexSlownik.__init__(self,fname)

	def textInListOut(self,text):
		for i in self.regexy:
			text=i.sub(self.regexy[i],text)
		lin=self.tokenizer(text)
		return self.metaProcess(lin)

	def textInTextOut(self,text):
		for i in self.regexy:
			text=i.sub(self.regexy[i],text)

		return text

	def processToken(self,token):
			return token

	def listInTextOut(self,list):
		out=self.metaProcess(list)
		return self.textInTextOut(self.tokenizer.desplit(out))

class StemmerSlownik(TextFileListSlownik):
	def __init__(self,fname):
		TextFileListSlownik.__init__(self,fname)
		self.mapperlen={}
		for i in self.forms:
			m=self.mapperlen.get(len(i),{})
			m[i]=True
			self.mapperlen[len(i)]=m

	def processToken(self,token):
		if token.find('+')>0: return token
		for i in range(len(token),0,-1):
			if token[-i:] in self.mapperlen.get(i,{}):
				ret=token[:len(token)-i]
				ret+=self.forms[token[-i:]]
				return ret+"+"+self.name
		return token

class StoplistSlownik(TextFileListSlownik):
	def __init__(self,fname):
		TextFileListSlownik.__init__(self,fname)

	def processToken(self,token):
		if token.find('+')>0: return token
		if token in self.forms or token.lower() in self.forms:
			return ""

class CompositeSlownik(Slownik):
    #def afterProcess(self):
    # 	for s in self.slowniki:
    #	    s.afterProcess()
    #def beforeProcess(self):
    #	for s in self.slowniki:
    #	    s.beforeProcess()
    pass

class CompositeListSlownik(CompositeSlownik):
	def __init__(self,*args):
		Slownik.__init__(self)
		self.slowniki=[]
		for s in args:
			self.slowniki.append(s)
		self.tokenizer=self.slowniki[0].tokenizer

	def process(self,list):
		ret=list
		for s in self.slowniki:
			ret=s.metaProcess(ret)
		return ret

class CompositeTokenSlownik(CompositeSlownik):
	def __init__(self,*args):
		Slownik.__init__(self)
		self.slowniki=[]
		for s in args:
			self.slowniki.append(s)
			self.tokenizer=self.slowniki[0].tokenizer

	def processToken(self,token):
		if token.find('+')>0: return token
		ret=""
		for s in self.slowniki:
			ret=s.processToken(token)
			if ret!=None and ret!=token:
				return ret

class CompositeTextSlownik(CompositeSlownik):
	def __init__(self,*args):
		Slownik.__init__(self)
		self.slowniki=[]
		for s in args:
			self.slowniki.append(s)
		self.tokenizer=self.slowniki[0].tokenizer

	def process(self,list):
		ret=self.slowniki[0].lito(list)
		for s in self.slowniki[1:-1]:
			ret=s.tito(ret)
		if len(self.slowniki)>1:
			ret=self.slowniki[-1].tilo(ret)
		return ret

class NotFoundSlownik(Slownik):
	def __init__(self,*args):
		Slownik.__init__(self)
	def processToken(self,token):
	    return token


class SlownikFactory(object):

	def __init__(self,prefix="dictionaries"):
		self.dirprefix=prefix+"/"
		self.legalclasses={}
		module=__import__('slowniki')
		for k in module.__dict__:
			if k.find('Slownik')>0:
				self.legalclasses[k]=module.__dict__[k]
		self.instances={}#flyweight

	def __getSlownik(self,name,fname):
		if (name,fname) not in self.instances:
			ret=self.legalclasses[name](fname)
			self.instances[(name,fname)]=ret
		return self.instances[(name,fname)]
	def __getattr__(self,name):
		prefix='get'
		if name.startswith(prefix) and name[len(prefix):] in self.legalclasses:
			return lambda x :  self.__getSlownik(name[len(prefix):],self.dirprefix+x)

	def getBasicSlownik(self):
		clp=self.getTextFileListSlownik('clp-list-up.txt')
		sjp=self.getTextFileListSlownik('sjp-list.txt')
		clppl=self.getTextFileListSlownik('clp-polonica.txt')
		sjppl=self.getTextFileListSlownik('sjp-polonica.txt')
		s1=self.getAbbreviationSlownik('skroty1.txt')
		s2=self.getAbbreviationSlownik('skroty2.txt')

		comp=CompositeTextSlownik(
			self.getContinousTextRegexSlownik('regex.txt'),
		CompositeTokenSlownik(
		    s1,
		    s2,
		    self.getRegexSlownik('regex.txt'),
		    self.getStoplistSlownik('stoplist-e.txt'),
		    self.getStoplistSlownik('stoplist-g.txt')
		),
		CompositeTokenSlownik(
		    self.getTextFileListSlownik('punctuation.txt'),
		    self.getStoplistSlownik('stoplist-e.txt'),
		    self.getStoplistSlownik('stoplist-g.txt'),
		    s1,
		    self.getAbbreviationSlownik('skroty2.txt'),
		    clp,
		    sjp,
		    self.getRegexSlownik('regex.txt'),
		    self.getTextFileListSlownik('english.txt'),
		    clppl,
		    sjppl,
		    self.getStemmerSlownik('stemmer1.txt'),
		    self.getStemmerSlownik('stemmer-reg1.txt'),
		    self.getStemmerSlownik('stemmer-reg2.txt')
		),
		NotFoundSlownik()
	    )

		return comp


if __name__=='__main__':
	a=TextFileListSlownik('dictionaries/simple-slownik.txt')
	t='Ala ma kota.'
	print t,"->",a.tilo(t)
	t=u"Źródła źródło zrodlo czesko-polsko-słowackiej polsko-węgierski biały(czarny)."
	tk=PunctuationTokenizer()
	print t
	for w in tk.split(t): print ">"+w+"<",
	print
	if (True):
		comp=SlownikFactory().getBasicSlownik()

		t="Prof. Lubaszewski jest kierownikiem GLK oraz instytutu na UJ."
		print t,"->",comp.tilo(t)
		t="Nie wiem czy chcemy Komorowskiego na prezydenta RP."
		ll=comp.tilo(t)
		print t,"->",ll
		for i in ll: print i

		t=u"Źródła źródło zrodlo czesko-polsko-słowackiej polsko-węgierski biały(czarny)."
		tk=PunctuationTokenizer()
		for w in tk.split(t): print w
		ll=comp.tilo(t)
		print t,"->",ll
		for i in ll: print i,i.lower()
		print comp.tilo(t)
	#f=open('w')
	#for l in f:
	#	print l.strip(),comp.tito(l)

#todo potencjalne
