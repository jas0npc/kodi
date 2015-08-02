import xbmc, xbmcplugin, xbmcaddon, xbmcgui, xbmcvfs
import os
import re
import sys

from addon.common.net import Net
from addon.common.addon import Addon
from metahandler import metahandlers


addon_id = 'plugin.video.tvrelease'
addon = Addon(addon_id, sys.argv)
Addon = xbmcaddon.Addon(addon_id)


sys.path.append( os.path.join( addon.get_path(), 'resources', 'lib' ) )
net = Net()

dbg = False

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer
cache = StorageServer.StorageServer(addon_id)


url = addon.queries.get('url', '')
name = addon.queries.get('name', '')
spare = addon.queries.get('spare', '')
mode = addon.queries.get('mode', '')
season = addon.queries.get('season', '')
episode = addon.queries.get('episode', '')

noImage = 'http://bento.cdn.pbs.org/hostedbento-prod/filer_public/_bento_media/img/no-image-available.jpg'


menu = [
    ('http://tv-release.net/?cat=TV-480p', '[COLOR red][B]*HD*480p[/B][/COLOR]'),
    ('http://tv-release.net/?cat=TV-720p', '[COLOR red][B]*HD*720p[/B][/COLOR]'),
    ('http://tv-release.net/?cat=TV-Mp4', '[COLOR red][B]Mp4[/B][/COLOR]'),
    ('http://tv-release.net/?cat=TV-XviD', '[COLOR red][B]XviD[/B][/COLOR]'),
    ]


def MAIN( menu ):
    liz=xbmcgui.ListItem(label='[COLOR gold]Resolver Settings[/COLOR]', thumbnailImage='https://raw.githubusercontent.com/Eldorados/script.module.urlresolver/master/icon.png')
    Transform()
    try:RealDebrid()
    except: pass
    for (url, name) in menu:
        addon.add_directory({'mode': 'index', 'url': url},{'title': name})
    addon.add_directory({'mode': 'search', 'url': url},{'title': 'Search'}, img='http://png-5.findicons.com/files/icons/117/radium/128/search.png')
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sys.argv[0]+'?mode=resolverSettings',isFolder=False,
                                listitem=liz)
    

def INDEX( url, spare ):
    addon.log( url )
    addon.log( spare )
    turl = url
    html = getHTML( url )

    r = re.search(r'current\'\>(\d+)\<', html, re.I)
    if r:
        total = re.search(r'\>(\d+)\<\/a\>\<\/span\>\<\/div\>', html)
        title = 'Page %s of %s Available' % ( r.group(1), total.group(1) )
        cat = re.search(r'(cat\=.*?)$', turl)
        
        if int(r.group(1)) >5:
            addon.add_directory({'mode': 'home', 'url': url},{'title': '<<< Home >>>'},is_folder=False)
        addon.add_item({},{'title': title}, is_folder=False)

    l = re.findall(r'\>(TV.*?)\<\/.*?\<a href=\'(http://tv-release.net/\d+\/.*?)\'', html, re.I)
    if l:
        totalitems = len(l)
        for cat, url in l:
            name = cleanName(url)
            if re.search(r'[\ss\d+e\d+|\s\d+\s\d+\s\d+]', name, re.I): types = 'episode'
            else: types = 'tvshow'

            if addon.get_setting('meta-data') == 'true':
                infoLabel = getMeta( name, types, spare )
                properties = {}
                episodes_unwatched = str(int(infoLabel['episode']) - infoLabel['playcount'])
                properties['UnWatchedEpisodes'] = episodes_unwatched
                properties['WatchedEpisodes'] = str(infoLabel['playcount'])

            else:
                infoLabel = {}
                infoLabel['title'] = name
                infoLabel['cover_url'] = noImage
                infoLabel['backdrop_url'] = noImage
                properties = None

            if spare:infoLabel['title'] = '['+cat+'] '+name
            else:infoLabel['title'] = name
            addon.add_item({'mode': 'resolve', 'url': url,'title': name, 'spare': spare},infoLabel,properties=properties,
                                total_items=totalitems, img=infoLabel['cover_url'], fanart=infoLabel['backdrop_url'])
    if r:
        cat = re.search(r'(cat\=.*?)$', turl)
        page = str(int(r.group(1))+1)
        if spare:
            try:search = re.search(r'\&s\=(.*?)$', turl).group(1)
            except:search = re.search(r'\/\?s\=(.*?)\&', turl).group(1)
            nextp = 'http://tv-release.net/index.php?page=%s&s=%s'%( page, search )
        else:
            if cat:
                page = str(int(r.group(1))+1)
                nextp = 'http://tv-release.net/index.php?page=%s&%s' %( page, cat.group(1))
        addon.add_directory({'mode': 'index', 'url': nextp, 'spare': spare},{'title': '>>Next Page>>>'})

        if int(page) >2:
            page = str(int(r.group(1))-1)
            if spare:
                try:search = re.search(r'\&s\=(.*?)$', turl).group(1)
                except:search = re.search(r'\/\?s\=(.*?)\&', turl).group(1)
                nextp = 'http://tv-release.net/index.php?page=%s&%s' %( page, search )
            else:
                nextp = 'http://tv-release.net/index.php?page=%s&%s' %( page, cat.group(1))
            addon.add_directory({'mode': 'index', 'url': nextp, 'spare': spare },{'title': '<<<Previous Page<<'})

            
    setView('episodes', 'episode-view')            
                


def cleanName(url):
    addon.log('CleanName: %s' % url)
    name = ''
    season = ''
    episode = ''
    title = ''
    year = ''
    month = ''
    day = ''
    name = url.rpartition('/')[2]

    r =re.split(r'\d+p', name)
    if r:
        name = r[0]
        r = re.search(r'(.*?)\ss(\d+)e(\d+)', name, re.I)

        if r:
            name = r.group(1)+', Season: %s Episode: %s' % ( r.group(2), r.group(3))
        if not r:
            r = re.search(r'(.*?)\s(\d+)\s(\d+)\s(\d+)\s', name, re.I)
            if r:
                name = r.group(1)+', Year: %s Month: %s Date: %s' % ( r.group(2), r.group(3), r.group(4))
            if not r:
                r = re.search(r'(.*?)\s(\d+)x(\d+)', name, re.I)
                if r:
                    name = r.group(1)+', Season: %s Episode: %s' % ( r.group(2), r.group(3))
                    

        name = re.sub(r'(?i)\s(\w\w)\,',  r' (\1),', name)
        
    return name
            
            

def getMeta( name, types, spare):
    if 'season' in name:
        types = 'episode'

    meta = []
    airdate = ''
    imdb = ''
    season = ''
    episode = ''
    tvdb_id = ''
    year = ''
    month = ''
    date = ''
    
    metaget = metahandlers.MetaData()

    r = re.search(r'(.*?),\sseason\:\s(\d+)\sepisode\:\s(\d+)$', name, re.I)
    if r:
        name = r.group(1)
        season = r.group(2)
        episode = r.group(3)
        
    if not r:
        r = re.search(r'(.*\s\d+)\se(\d+)\s', name, re.I)
        if r:
            name = r.group(1)
            episode = r.group(2)
        if not r:
            r = re.search(r'(.*?)\,\syear\:', name, re.I)
            if r:
                name = r.group(1)

    meta = metaget.get_meta('tvshow', name=name, year='')
    if meta['cover_url'] == '':
        meta['cover_url'] = noImage
    if meta['backdrop_url'] == '':
        meta['backdrop_url'] = noImage

    if spare:
        if types == 'episode':
            meta = metaget.get_episode_meta( tvshowtitle=name, imdb_id=meta['imdb_id'],
                                             season=season, episode=episode, air_date='' )
        

    return meta

def RESOLVE(url):
    addon.log('RESOLVE: %s' % url)
    sources = []
    
    html = getHTML( url )
    import urlresolver
    for links in re.finditer(r'\'\>(http.*?)\<', html, re.I):
        hoster = re.search(r'\/\/(.*?)\/', re.sub(r'www\.', '',links.group(1))).group(1)
        hostedMedia = urlresolver.HostedMediaFile(url=links.group(1), title=hoster)
        sources.append(hostedMedia)

    source = urlresolver.choose_source(sources)
    if source:
        stream_url=source.resolve()
        playStreamUrl(stream_url)
    else: return

def search(url):
    addon.log('Search')

    keyboard = xbmc.Keyboard()
    keyboard.setHeading('Search TV Shows')
    
    keyboard.doModal()
    
    if keyboard.isConfirmed():
        searcht=keyboard.getText()
        if not searcht:
            addon.show_ok_dialog(['empty search not allowed'.title()], 'TVRelease')
            search(url)
    else:
        MAIN( menu )
    url = 'http://tv-release.org/?s=%s&cat='%searcht
    spare = 'search'
    print url
    print spare 
    INDEX( url, spare )
    
        
    

    
def playStreamUrl(stream_url):
    listitem = xbmcgui.ListItem(path=str(stream_url), iconImage='', thumbnailImage='')
    listitem.setProperty('IsPlayable', 'true')
    listitem.setPath(str(stream_url))
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
    return True

''' Why recode whats allready written and works well,
    Thanks go to Eldrado for it '''

def setView(content, viewType):
    if content:
        xbmcplugin.setContent(int(sys.argv[1]), content)
    if addon.get_setting('auto-view') == 'true':
        xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.get_setting(viewType) )

    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RATING )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_PROGRAM_COUNT )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING )
    


def Transform():
    if addon.get_setting('transform') == 'true':
        return
    if xbmcvfs.exists(xbmc.translatePath('special://masterprofile/sources.xml')):
        with open(xbmc.translatePath(os.path.join( addon.get_path(), 'resources', 'sourcesapp.xml'))) as f:
            sourcesapp = f.read()
            f.close()
        with open(xbmc.translatePath('special://masterprofile/sources.xml'), 'r+') as f:
            my_file = f.read()
            if re.search(r'http://transform.mega-tron.tv/', my_file):
                addon.log('Transform Source Found in sources.xml, Not adding.')
                return
            addon.log('Adding Transform source in sources.xml')
            my_file = re.split(r'</files>\n</sources>\n', my_file)
            my_file = my_file[0]+sourcesapp
            f.seek(0)
            f.truncate()
            f.write(my_file)
            f.close()
            Addon.setSetting(id='transform', value='true')
            

    else:
        xbmcvfs.copy(xbmc.translatePath(os.path.join( addon.get_path(), 'resources', 'sources.xml')),
                       xbmc.translatePath('special://masterprofile/sources.xml'))
        Addon.setSetting(id='transform', value='true')


def RealDebrid():
    rdv = addon.get_setting('realdebrid-video')
    addon.log('RealDebrid Video setting: %s'% rdv)
    
    if addon.get_setting('realdebrid-video') == 'true':
        return
    resolverSettings = xbmc.translatePath('special://masterprofile/addon_data/script.module.urlresolver/settings.xml')
    with open(resolverSettings, 'r') as f:
        my_file = f.read()
        f.close()
        r = re.search(r'RealDebridResolver_login\"\svalue\=\"false\"', my_file, re.I)
        
        if r:
            xbmcgui.Dialog().ok("TvRelease Realdebrid Info Video", "@veedubt25 Has made a video on HOW realdebrid works",
                                "You will ONLY see this ONCE")
            xbmc.executebuiltin("PlayMedia(plugin://plugin.video.youtube/?action=play_video&videoid=s-C4DdG4FF0&quality=720p)")
            Addon.setSetting(id='realdebrid-video', value='true')
        else:
            return
    
                                          
def getHTML( url ):
    headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
               'Accept-Encoding': 'gzip, deflate, sdch',
               'Accept-Language': 'en-GB,en-US;q=0.8,en;q=0.6', 'Host': 'tv-release.net',
               'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'DNT': '1',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.94 Safari/537.36'}

    html = net.http_GET(url, headers).content

    return html

if mode== 'main':
    MAIN( menu )
elif mode == 'index':
    INDEX( url, spare )
elif mode == 'resolve':
    RESOLVE(url)
elif mode == 'home':
    xbmc.executebuiltin("XBMC.Container.Update(plugin://plugin.video.tvrelease)")
elif mode == 'resolverSettings':
    import urlresolver
    urlresolver.display_settings()
elif mode == 'search':
    search(url)
                                


setView(None, 'default-view')
xbmcplugin.endOfDirectory(int(sys.argv[1]))
