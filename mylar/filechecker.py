#/usr/bin/env python
#  This file is part of Mylar.
#
#  Mylar is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mylar is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mylar.  If not, see <http://www.gnu.org/licenses/>.

import os
import os.path
import pprint
import subprocess
import re
import logger
import mylar
import sys

def file2comicmatch(watchmatch):
    #print ("match: " + str(watchmatch))
    pass

def listFiles(dir,watchcomic,AlternateSearch=None,manual=None):

    # use AlternateSearch to check for filenames that follow that naming pattern
    # ie. Star Trek TNG Doctor Who Assimilation won't get hits as the 
    # checker looks for Star Trek TNG Doctor Who Assimilation2 (according to CV)
    
    # we need to convert to ascii, as watchcomic is utf-8 and special chars f'it up
    u_watchcomic = watchcomic.encode('ascii', 'ignore').strip()    
    logger.fdebug('comic: ' + watchcomic)
    basedir = dir
    logger.fdebug('Looking in: ' + dir)
    watchmatch = {}
    comiclist = []
    comiccnt = 0
    not_these = ['#',
               ',',
               '\/',
               ':',
               '\;',
               '.',
               '-',
               '\!',
               '\$',
               '\%',
               '\+',
               '\'',
               '\?',
               '\@']

    issue_exceptions = ['AU',
                      'AI', 
                      'A',
                      'B',
                      'C']

    for item in os.listdir(basedir):
        if item == 'cover.jpg' or item == 'cvinfo': continue
        #print item
        #subname = os.path.join(basedir, item)
        subname = item
        #versioning - remove it
        subsplit = subname.replace('_', ' ').split()
        volrem = None
        for subit in subsplit:
            if subit[0].lower() == 'v':
                vfull = 0
                if subit[1:].isdigit():
                    #if in format v1, v2009 etc...
                    if len(subit) > 3:
                        # if it's greater than 3 in length, then the format is Vyyyy
                        vfull = 1 # add on 1 character length to account for extra space
                    subname = re.sub(subit, '', subname)
                    volrem = subit
                elif subit.lower()[:3] == 'vol':
                    #if in format vol.2013 etc
                    #because the '.' in Vol. gets removed, let's loop thru again after the Vol hit to remove it entirely
                    logger.fdebug('volume indicator detected as version #:' + str(subit))
                    subname = re.sub(subit, '', subname)
                    volrem = subit

        #remove the brackets..
        subnm = re.findall('[^()]+', subname)
        if len(subnm):
            logger.fdebug("detected invalid filename - attempting to detect year to continue")
            subname = re.sub('(.*)\s+(19\d{2}|20\d{2})(.*)', '\\1 (\\2) \\3', subname)
            subnm = re.findall('[^()]+', subname)

        subname = subnm[0]
        logger.fdebug('subname no brackets: ' + str(subname))
        subname = re.sub('\_', ' ', subname)
        nonocount = 0
        charpos = 0
        detneg = "no"
        for nono in not_these:
            if nono in subname:
                subcnt = subname.count(nono)
                charpos = indices(subname,nono) # will return a list of char positions in subname
                #print "charpos: " + str(charpos)
                if nono == '-':
                    i=0
                    while (i < len(charpos)):
                        for i,j in enumerate(charpos):
                            #print i,j
                            if subname[j+1:j+2].isdigit():
                                logger.fdebug('possible negative issue detected.')
                                nonocount = nonocount + subcnt - 1
                                detneg = "yes"                                
                            if '-' in watchcomic and i < len(watchcomic):
                                logger.fdebug('- appears in series title.')
                        i+=1
                    if detneg == "no": 
                        subname = re.sub(str(nono), ' ', subname)
                        nonocount = nonocount + subcnt
                #logger.fdebug(str(nono) + " detected " + str(subcnt) + " times.")
                # segment '.' having a . by itself will denote the entire string which we don't want
                elif nono == '.':
                    x = 0
                    fndit = 0
                    dcspace = 0
                    while x < subcnt:
                        fndit = subname.find(nono, fndit)
                        if subname[fndit-1:fndit].isdigit() and subname[fndit+1:fndit+2].isdigit():
                            logger.fdebug('decimal issue detected.')
                            dcspace+=1
                        x+=1
                    if dcspace == 1:
                        nonocount = nonocount + subcnt + dcspace                    
                    else:
                        subname = re.sub('\.', ' ', subname)
                        nonocount = nonocount + subcnt - 1 #(remove the extension from the length)
                else:
                    #this is new - if it's a symbol seperated by a space on each side it drags in an extra char.
                    x = 0
                    fndit = 0
                    blspc = 0
                    while x < subcnt:
                        fndit = subname.find(nono, fndit)
                        #print ("space before check: " + str(subname[fndit-1:fndit]))
                        #print ("space after check: " + str(subname[fndit+1:fndit+2]))
                        if subname[fndit-1:fndit] == ' ' and subname[fndit+1:fndit+2] == ' ':
                            logger.fdebug('blankspace detected before and after ' + str(nono))
                            blspc+=1
                        x+=1
                    subname = re.sub(str(nono), ' ', subname)
                    nonocount = nonocount + subcnt + blspc
        #subname = re.sub('[\_\#\,\/\:\;\.\-\!\$\%\+\'\?\@]',' ', subname)
        modwatchcomic = re.sub('[\_\#\,\/\:\;\.\-\!\$\%\'\?\@]', ' ', u_watchcomic)
        detectand = False
        detectthe = False
        modwatchcomic = re.sub('\&', ' and ', modwatchcomic)
        if ' the ' in modwatchcomic.lower():
            modwatchcomic = re.sub("\\bthe\\b", "", modwatchcomic.lower())
            logger.fdebug('new modwatchcomic: ' + str(modwatchcomic))
            detectthe = True
        modwatchcomic = re.sub('\s+', ' ', str(modwatchcomic)).strip()
        if '&' in subname:
            subname = re.sub('\&', ' and ', subname) 
            detectand = True
        if ' the ' in subname.lower():
            subname = re.sub("\\bthe\\b", "", subname.lower())
            detectthe = True
        subname = re.sub('\s+', ' ', str(subname)).strip()

        AS_Alt = []
        if AlternateSearch is not None:
            chkthealt = AlternateSearch.split('##')
            if chkthealt == 0:
                AS_Alternate = AlternateSearch
            for calt in chkthealt:
                AS_Alternate = re.sub('##','',calt)
                #same = encode.
                u_altsearchcomic = AS_Alternate.encode('ascii', 'ignore').strip()
                altsearchcomic = re.sub('[\_\#\,\/\:\;\.\-\!\$\%\+\'\?\@]', '', u_altsearchcomic)
                altsearchcomic = re.sub('\&', ' and ', altsearchcomic)
                altsearchcomic = re.sub('\s+', ' ', str(altsearchcomic)).strip()       
                AS_Alt.append(altsearchcomic)
        else:
            #create random characters so it will never match.
            altsearchcomic = "127372873872871091383 abdkhjhskjhkjdhakajhf"
            AS_Alt.append(altsearchcomic)
        #if '_' in subname:
        #    subname = subname.replace('_', ' ')
        logger.fdebug('watchcomic:' + str(modwatchcomic) + ' ..comparing to found file: ' + str(subname))
        if modwatchcomic.lower() in subname.lower() or any(x.lower() in subname.lower() for x in AS_Alt):#altsearchcomic.lower() in subname.lower():
            comicpath = os.path.join(basedir, item)
            logger.fdebug( modwatchcomic + ' - watchlist match on : ' + comicpath)
            comicsize = os.path.getsize(comicpath)
            #print ("Comicsize:" + str(comicsize))
            comiccnt+=1

            stann = 0
            if 'annual' in subname.lower():
                logger.fdebug('Annual detected - proceeding')
                jtd_len = subname.lower().find('annual')
                cchk = modwatchcomic
            else:
                if modwatchcomic.lower() in subname.lower():
                    cchk = modwatchcomic
                else:
                    cchk_ls = [x for x in AS_Alt if x.lower() in subname.lower()]
                    cchk = cchk_ls[0]
                    #print "something: " + str(cchk)

                logger.fdebug('we should remove ' + str(nonocount) + ' characters')                

                findtitlepos = subname.find('-')
                if charpos != 0:
                    logger.fdebug('detected ' + str(len(charpos)) + ' special characters')
                    i=0
                    while (i < len(charpos)):
                        for i,j in enumerate(charpos):
                            #print i,j
                            #print subname
                            #print "digitchk: " + str(subname[j:])
                            if j >= len(subname):
                                logger.fdebug('end reached. ignoring remainder.')
                                break
                            elif subname[j:] == '-':
                                if i <= len(subname) and subname[i+1].isdigit():
                                    logger.fdebug('negative issue detected.')
                                    #detneg = "yes"
                            elif j > findtitlepos:
                                if subname[j:] == '#':
                                   if subname[i+1].isdigit():
                                        logger.fdebug('# detected denoting issue#, ignoring.')
                                   else: 
                                        nonocount-=1
                                elif '-' in watchcomic and i < len(watchcomic):
                                   logger.fdebug('- appears in series title, ignoring.')
                                else:                             
                                   logger.fdebug('special character appears outside of title - ignoring @ position: ' + str(charpos[i]))
                                   nonocount-=1
                        i+=1

            #remove versioning here
            if volrem != None:
                jtd_len = len(cchk)# + len(volrem)# + nonocount + 1 #1 is to account for space btwn comic and vol #
            else:
                jtd_len = len(cchk)# + nonocount

            logger.fdebug('nonocount [' + str(nonocount) + '] cchk [' + cchk + '] length [' + str(len(cchk)) + ']')

            #if detectand:
            #    jtd_len = jtd_len - 2 # char substitution diff between & and 'and' = 2 chars
            #if detectthe:
            #    jtd_len = jtd_len - 3  # char subsitiution diff between 'the' and '' = 3 chars

            #justthedigits = item[jtd_len:]

            logger.fdebug('final jtd_len to prune [' + str(jtd_len) + ']')
            logger.fdebug('before title removed from FILENAME [' + str(item) + ']')
            logger.fdebug('after title removed from FILENAME [' + str(item[jtd_len:]) + ']')
            logger.fdebug('creating just the digits using SUBNAME, pruning first [' + str(jtd_len) + '] chars from [' + subname + ']')

            justthedigits = subname[jtd_len:].strip()

            logger.fdebug('after title removed from SUBNAME [' + justthedigits + ']')

            #remove the title if it appears
            #findtitle = justthedigits.find('-')
            #if findtitle > 0 and detneg == "no":
            #    justthedigits = justthedigits[:findtitle]
            #    logger.fdebug("removed title from name - is now : " + str(justthedigits))

            tmpthedigits = justthedigits
            justthedigits = justthedigits.split(' ', 1)[0]

 
            #if the issue has an alphanumeric (issue_exceptions, join it and push it through)
            logger.fdebug('JUSTTHEDIGITS [' + justthedigits + ']' )
            if justthedigits.isdigit():
                digitsvalid = "true"
            else:
                digitsvalid = "false"

            if justthedigits.lower() == 'annual':
                logger.fdebug('ANNUAL ['  + tmpthedigits.split(' ', 1)[1] + ']')
                justthedigits += ' ' + tmpthedigits.split(' ', 1)[1]
                digitsvalid = "true"
            else:
                
                try:
                    if tmpthedigits.split(' ', 1)[1] is not None:
                        poss_alpha = tmpthedigits.split(' ', 1)[1]
                        for issexcept in issue_exceptions:
                            if issexcept.lower() in poss_alpha.lower() and len(poss_alpha) <= len(issexcept):
                                justthedigits += poss_alpha
                                logger.fdebug('ALPHANUMERIC EXCEPTION. COMBINING : [' + justthedigits + ']')
                                digitsvalid = "true"
                                break
                except:
                    pass

            logger.fdebug('final justthedigits [' + justthedigits + ']')
            if digitsvalid == "false": 
                logger.fdebug('Issue number not properly detected...ignoring.')
                continue            
            

            if manual is not None:
                #this is needed for Manual Run to determine matches
                #without this Batman will match on Batman Incorporated, and Batman and Robin, etc..
                logger.fdebug('modwatchcomic = ' + modwatchcomic.lower())
                logger.fdebug('subname = ' + subname.lower())
                comyear = manual['SeriesYear']
                issuetotal = manual['Total']
                logger.fdebug('SeriesYear: ' + str(comyear))
                logger.fdebug('IssueTotal: ' + str(issuetotal))

                #set the issue/year threshold here.
                #  2013 - (24issues/12) = 2011.
                minyear = int(comyear) - (int(issuetotal) / 12)
                
                #subnm defined at being of module.
                len_sm = len(subnm)

                #print ("there are " + str(lenm) + " words.")
                cnt = 0
                yearmatch = "false"

                while (cnt < len_sm):
                    if subnm[cnt] is None: break
                    if subnm[cnt] == ' ':
                        pass
                    else:
                        logger.fdebug(str(cnt) + ". Bracket Word: " + str(subnm[cnt]))

                    if subnm[cnt][:-2] == '19' or subnm[cnt][:-2] == '20':
                        logger.fdebug("year detected: " + str(subnm[cnt]))
                        result_comyear = subnm[cnt]
                        if int(result_comyear) >= int(minyear):
                            logger.fdebug(str(result_comyear) + ' is within the series range of ' + str(minyear) + '-' + str(comyear))
                            yearmatch = "true"
                            break
                        else:
                            logger.fdebug(str(result_comyear) + ' - not right - year not within series range of ' + str(minyear) + '-' + str(comyear))
                            yearmatch = "false"
                            break
                    cnt+=1

                if yearmatch == "false": continue

                #tmpitem = item[:jtd_len]
                # if it's an alphanumeric with a space, rejoin, so we can remove it cleanly just below this.
                substring_removal = None
                poss_alpha = subname.split(' ')[-1:]
                logger.fdebug('poss_alpha: ' + str(poss_alpha))
                logger.fdebug('lenalpha: ' + str(len(''.join(poss_alpha))))
                for issexcept in issue_exceptions:
                    if issexcept.lower()in str(poss_alpha).lower() and len(''.join(poss_alpha)) <= len(issexcept):
                        #get the last 2 words so that we can remove them cleanly
                        substring_removal = ' '.join(subname.split(' ')[-2:])
                        substring_join = ''.join(subname.split(' ')[-2:])
                        logger.fdebug('substring_removal: ' + str(substring_removal))
                        logger.fdebug('substring_join: ' + str(substring_join))
                        break

                if substring_removal is not None:
                    sub_removed = subname.replace('_', ' ').replace(substring_removal, substring_join)
                else:
                    sub_removed = subname.replace('_', ' ')
                logger.fdebug('sub_removed: ' + str(sub_removed))
                split_sub = sub_removed.rsplit(' ',1)[0].split(' ')  #removes last word (assuming it's the issue#)
                split_mod = modwatchcomic.replace('_', ' ').split()   #batman
                logger.fdebug('split_sub: ' + str(split_sub))
                logger.fdebug('split_mod: ' + str(split_mod))

                x = len(split_sub)-1
                scnt = 0
                if x > len(split_mod)-1:
                    logger.fdebug('number of words do not match...aborting.')
                else:
                    while ( x > -1 ):
                        print str(split_mod[x]) + ' comparing to ' + str(split_mod[x])
                        if str(split_sub[x]).lower() == str(split_mod[x]).lower():
                            scnt+=1
                            logger.fdebug('word match exact. ' + str(scnt) + '/' + str(len(split_mod)))
                        x-=1

                wordcnt = int(scnt)
                logger.fdebug('scnt:' + str(scnt))
                totalcnt = int(len(split_mod))
                logger.fdebug('split_mod length:' + str(totalcnt))
                try:
                    spercent = (wordcnt/totalcnt) * 100
                except ZeroDivisionError:
                    spercent = 0
                logger.fdebug('we got ' + str(spercent) + ' percent.')
                if int(spercent) >= 80:
                    logger.fdebug("this should be considered an exact match.")
                else:
                    logger.fdebug('failure - not an exact match.')
                    continue

            comiclist.append({
                 'ComicFilename':           item,
                 'ComicLocation':           comicpath,
                 'ComicSize':               comicsize,
                 'JusttheDigits':           justthedigits
                 })
            watchmatch['comiclist'] = comiclist
        else:
            pass
            #print ("directory found - ignoring")
    logger.fdebug('you have a total of ' + str(comiccnt) + ' ' + watchcomic + ' comics')
    watchmatch['comiccount'] = comiccnt
    #print watchmatch
    return watchmatch

def validateAndCreateDirectory(dir, create=False):
    if os.path.exists(dir):
        logger.info('Found comic directory: ' + dir)
        return True
    else:
        logger.warn('Could not find comic directory: ' + dir)
        if create:
            if dir.strip():
                logger.info('Creating comic directory (' + str(mylar.CHMOD_DIR) + ') : ' + dir)
                try:
                    permission = int(mylar.CHMOD_DIR, 8)
                    os.umask(0) # this is probably redudant, but it doesn't hurt to clear the umask here.
                    os.makedirs(dir, permission )
                except OSError:
                    raise SystemExit('Could not create data directory: ' + mylar.DATA_DIR + '. Exiting....')
                return True
            else:
                logger.warn('Provided directory is blank, aborting')
                return False
    return False


def indices(string, char):
    return [ i for i,c in enumerate(string) if c == char ]

