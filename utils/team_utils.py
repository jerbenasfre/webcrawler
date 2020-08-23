from crawler.datastore import DataStore
from urllib.parse import urlparse

import re
from urllib.parse import urljoin

import redis
import tldextract
import json

from utils.cacheRobotParser import CacheRobotFileParser

r = redis.Redis(host="localhost",port=6379,db=0, decode_responses=True)

#robotsCheck ="robotsDict"
mostTokensUrl="mostTokens"
setDomainCount = "setDomainCount"
TOKEN_COUNT_NAME = "tokenCount"
TOKEN_COUNT_KEY = "dictKey"
HASH_SAME = "hashSame"
blackList = "blackListed"
visitedURL = "urls"

four0four = ""


icsDomains = {}#Added to keep track of specifically ics Domains

'''
Finds the domain/subdomain of url gets robots.txt
Stores the domain/subdomain as a key in robotsCheck
I think we just need to call subdomain(url) to get a key, because all urls should have the 5 seeds as their domain.
May remove adding domain to robotchecks part.

Thought process: robots.txt is found in the root page which is usually a domain or subdomain. In order to check if a url is allowed or not, 
just find its domain/subdomain and look at the disallowed section.
'''
def robotsTxtParse(url, config, logger):
    # Finds the robot.txt of a domain and subdomain(if one exists) and
    # Stores it in DataStore.RobotChecks
    scheme = urlparse(url).scheme #scheme needed to read robots.txt

    domain = getDomain(url)
    #val=r.hget(robotsCheck,"bhh").decode('utf-8')
    if domain != '' and domain not in DataStore.robotsCheck and domain != 'uci.edu':
    #if domain != '' and domain not in r.hexists(robotsCheck, domain):
        robotTxtUrl = f"{scheme}://{domain}/robots.txt"
        robot = CacheRobotFileParser(config, logger)
        robot.set_url(robotTxtUrl)
        robot.read()
        #r.hset(robotsCheck, domain, robot)
        DataStore.robotsCheck[domain] = robot

    subdomain = getSubDomain(url)
    if subdomain != '' and subdomain not in DataStore.robotsCheck:
    #if subdomain != '' and not r.hexists(robotsCheck,subdomain):
        robotTxtUrl = f"{scheme}://{subdomain}/robots.txt"
        robot = CacheRobotFileParser(config, logger)
        robot.set_url(robotTxtUrl)
        robot.read()
        #r.hset(robotsCheck, subdomain, robot)
        DataStore.robotsCheck[subdomain] = robot

def robotsTxtParseSeeds(config, logger):
    # Stores the robot.txt of the seed urls in DataStore.RobotChecks
    seedUrls = ['https://today.uci.edu/department/information_computer_sciences/',
    'https://www.ics.uci.edu',
    'https://www.cs.uci.edu',
    'https://www.informatics.uci.edu',
    'https://www.stat.uci.edu']
    for seedUrl in seedUrls:
        scheme = urlparse(seedUrl).scheme
        domain = getSubDomain(seedUrl)
        robotTxtUrl = f"{scheme}://{domain}/robots.txt"
        robot = CacheRobotFileParser(config, logger)
        robot.set_url(robotTxtUrl)
        robot.read()
        DataStore.robotsCheck[domain] = robot
        #r.hset(robotsCheck, domain, robot)

def robotsAllowsSite(subdomain, url):
    if subdomain in DataStore.robotsCheck.keys():
    #if r.hexists(robotsCheck,subdomain):
        #robot = r.hget(robotsCheck,subdomain)#.decode('utf-8')
        robot = DataStore.robotsCheck[subdomain]
        return robot.can_fetch("*", url)

    return True #if robots.txt not found, then we can scrape freely


### CHANGED TO ADD SUFFIX TO DOMAIN
def getDomain(url):
    # Gets the domain or subdomain of a url and returns it.
    ext = tldextract.extract(url)
    #domainUrl = ext.domain
    domainUrl = f"{ext.domain}.{ext.suffix}"#'.'.join([domainUrl, ext.suffix])

    return domainUrl

### CHANGED TO ADD SUFFIX TO DOMAIN
def getSubDomain(url):
    ext = tldextract.extract(str(url))
    domainUrl = ''
    if ext.subdomain == '':  # Returns url with subdomain attached.
        return f"{ext.domain}.{ext.suffix}"#'.'.join([ext.domain, ext.suffix])
    #domainUrl = '.'.join(ext[:2])
    domainUrl = f"{ext.subdomain}.{ext.domain}.{ext.suffix}"#'.'.join([domainUrl, ext.suffix])

    return domainUrl


def returnFullURL(parent_url, strInput):
    parsed_uri = urlparse(parent_url)
    result = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)   #remove slash

    if (strInput.strip() == "/"):
        return ""
    if (strInput.strip() == "#"):
        return ""
    if ("#" in strInput.strip() and removeFragment(strInput) == ""):
        return ""
    else:
        return urljoin(result, strInput)


def incrementSubDomain(strDomain):
    parsed_uri = urlparse(strDomain)
    result = '{uri.netloc}'.format(uri=parsed_uri)   #remove slash at end
    result = getSubDomain(result)
    result = result.replace("www.", "")

    if r.hexists(setDomainCount,result):
        val = r.hget(setDomainCount,result)
        val = int(val)
        val += 1
        r.hset(setDomainCount,result,val)
    else:
        r.hset(setDomainCount,result,1)

    #r.hset(setDomainCount)
    #DataStore.subDomainCount[result] = DataStore.subDomainCount.get(result, 0) + 1


def tokenize(url, rawText):
    listTemp = re.split(r"[^a-z0-9']+", rawText.lower())

    #if r.hget(mostTokensUrl, ):
    if (DataStore.mostTokensUrl[1] < len(listTemp)):
        DataStore.mostTokensUrl[0] = url
        DataStore.mostTokensUrl[1] = len(listTemp)
        # cant find a workaround so im just storing it locally and in the database
        r.delete(mostTokensUrl)
        r.hset(mostTokensUrl,url,len(listTemp))


    ##### STORE word counts in dictionary inside of redis #####
    dictCounter = dict()
    dictTEMP = dict()

    if not r.hexists(TOKEN_COUNT_NAME, TOKEN_COUNT_KEY):
        r.hset(TOKEN_COUNT_NAME, TOKEN_COUNT_KEY, json.dumps(dictCounter).encode('utf-8'))
        dictCounter = r.hgetall(TOKEN_COUNT_NAME)
    else:
        dictCounter = r.hgetall(TOKEN_COUNT_NAME)

    dictTEMP = dict(json.loads(dictCounter[TOKEN_COUNT_KEY]))

    boolOnly = False
    if len(dictTEMP) > 0:
        boolOnly = True
        dictTEMP = dict(json.loads(dictTEMP[TOKEN_COUNT_KEY]))

    for word in listTemp:
        if not word in dictTEMP:
            dictTEMP[word] = 1
        else:
            dictTEMP[word] += 1

    dictCounter[TOKEN_COUNT_KEY] = json.dumps(dictTEMP)

    # save back into redis
    r.hset(TOKEN_COUNT_NAME, TOKEN_COUNT_KEY, json.dumps(dictCounter))


    if (len(listTemp) == 0):
        r.sadd(blackList,url)
        #DataStore.blackList.add(url)


#### ADDED IF STATEMENTS TO CHECK FOR CALENDAR
#if url has been blacklisted before
def isBlackListed(str):
    if r.sismember(blackList,str):
    #if str in DataStore.blackList:
        return True
    return False

### *DO NOT* ADD isSameHash() to isValid() ###
def isSameHash(str):
    if r.sismember(HASH_SAME,str):
        return True
    return False

# #supposed to split if two urls combined
# # https://canvas.eee.uci.edu/courses/23516/files/folder/lectures?preview-8330088 returns empty when run on
# def extractURL(str):
#     try:
#         url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str)
#         if ',' in url[0]:
#             url= url[0].split(',')
#         return url
#     except:
#         return ""

def removeFragment(str):
    str = str.split('#')[0]
    return str


# def hashUrl(url)->None:
#     # 2/6/2020 Function takes in a url and finds the hash for it. Adds the hash and url into a dic
#     normalizedUrl = normalize(url)
#     DataStore.hashTable[get_urlhash(normalizedUrl)] = url

def ifConsideredSpam(str):
    try:
        str = str.split('?')[1]
        str = str.split('=')[0]
        if "replytocom" in str:
            return True
    except:
        return False
    return False

def ifInUCIDomain(str):
    if 'today.uci.edu/department/information_computer_sciences' in str:
        return True
    str = getSubDomain(str)
    if '.ics.uci.edu'in str or '/ics.uci.edu' in str:
        return True
    if '.cs.uci.edu' in str or '/cs.uci.edu' in str:
        return True
    if '.informatics.uci.edu' in str or '/informatics.uci.edu' in str:
        return True
    if '.stat.uci.edu' in str or '/stat.uci.edu' in str:
        return True
    return False

def is_validDEFAULT(url):
    try:
        parsed = urlparse(url)
        subdomain = getSubDomain(url)#key = '://'.join([tutils.getSubDomain(url), parsed.scheme])

        if parsed.scheme not in set(["http", "https"]):
            return False

        ### COMMENT BACK IN WHEN FINISHED ###
        if not robotsAllowsSite(subdomain, url):
            return False

        #if url in DataStore.blackList:
        #if r.sismember(visitedURL,url):
            #return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|jpg|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4|rvi"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
    except TypeError:
        print ("TypeError for ", parsed)
        return False

        # if subdomain in DataStore.robotsCheck.keys():
        # #if r.hexists(robotsCheck,subdomain):
        #     #robot = r.hget(robotsCheck,subdomain).decode('utf-8')
        #     robot =  DataStore.robotsCheck[subdomain]
        #     return robot.can_fetch("*", url)

#is url valid
def isValid(str):
    if isBlackListed(str):
        return False
    if r.sismember(visitedURL, str):
        return False
    if not is_validDEFAULT(str):
        return False
    if ifConsideredSpam(str):
        return False
    if not ifInUCIDomain(str):
        return False
    if badUrl(str):
        return False
    if ifRepeatPath(str):
        return False
    return True

def badUrl(str):
    if "search" in str:
        return True
    if "calendar" in str:
        return True
    if "graphics" in str:
        return True
    if "color" in str:
        return True
    if "ppt" in str:
        return True
    if "pdf" in str:
        return True
    if len(str)>150:
        return True
    if "login" in str:
        return True
    if "://cbcl" in str:
        return True
    if "www.amazon.com" in str:
        return True
    if "events/category/boothing" in str:
        return True
    if "difftype=sidebyside" in str:
        return True
    if 'https://today.uci.edu/department/information_computer_sciences/calendar' in str:
        return True
    if 'https://www.ics.uci.edu/~eppstein/pix/chron.html' in str:
        return True
    if ".htm" in str:
        return True
    if '.zip' in str:
        return True
    if "gallery" in str:
        return True
    if "signup" in str:
        return True
    if "/event/" in str:
        return True
    if "events/" in str:
        return True
    if "wics-" in str:
        return True
    if "share" in str:
        return True
    if "slides" in str:
        return True
    if ".txt" in str:
        return True
    if 'flamingo.' in str:
        return True
    if 'facebook'in str:
        return True
    if 'twitter' in str:
        return True
    if '//swiki.ics'in str:
        return True
    if 'eppstein/pix' in str:
        return True

    return False

def ifRepeatPath(input):
    origUrl = input
    path = urlparse(input).path.strip()

    arrsplit = path.split("/")
    iCount = 0
    strcurrent = ""
    loopiter = 0

    for itoken in arrsplit:
        if(itoken.strip() == "/"):
            arrsplit = arrsplit[1:]
            continue
        if (itoken.strip() == ""):
            arrsplit = arrsplit[1:]
            continue

        strcurrent = arrsplit[0]
        arrsplit = arrsplit[1:]

        for second in arrsplit:
            if (second == strcurrent):
                r.sadd(blackList, origUrl)
                return True
    return False