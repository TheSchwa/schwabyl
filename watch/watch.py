import os,subprocess,socket,pickle,time
import datetime as dt

from sibyl.lib.decorators import botconf,botinit,botcmd,botidle

from tracker import Tracker

ROUTER = '192.168.1.1'
WATCHFILE = '/home/sibyl/sibyl/data/watch/log.pickle'

@botconf
def conf(bot):
  return {'name':'notify',
          'default':True,
          'parse':bot.conf.parse_bool}

@botinit
def init(bot):
  bot.add_var('host_names',{},persist=True)
  bot.add_var('host_pings',{},persist=True)
  bot.add_var('host_tracker',Tracker())
  bot.host_tracker.load(WATCHFILE)
  bot.add_var('host_pending',{},persist=True)
  bot.host_tracker.pending = bot.host_pending

@botcmd(hidden=True)
def watch(bot,mess,args):
  """track hosts on the LAN - hosts (list|show|add|remove)"""

  if len(args)<1 or args[0] not in ('list','add','remove','show'):
    args = ['list']

  if args[0]=='list':
    to = mess.get_from()
    if not bot.host_names:
      return 'No watches'

    hosts = [name for (ip,name) in bot.host_names.items()
        if bot.host_pings.get(ip,3)<3]
    if hosts:
      bot.send('Online: '+', '.join(hosts),to)

    hosts = [name for (ip,name) in bot.host_names.items()
        if bot.host_pings.get(ip,0)==3]
    if hosts:
      bot.send('Offline: '+', '.join(hosts),to)

    hosts = [name for (ip,name) in bot.host_names.items()
        if ip not in bot.host_pings]
    if hosts:
      bot.send('Pending: '+', '.join(hosts),to)

    return

  elif args[0]=='show':
    if len(args)<2:
      return bot.host_names
    elif args[1] in bot.host_names:
      return bot.host_names[args[1]]
    elif args[1] in bot.host_names.values():
      return ', '.join([ip for (ip,name) in bot.host_names.items() if name==args[1]])
    else:
      return 'Unknown hostname or IP'

  elif args[0]=='add':
    if len(args)<3:
      return 'You must specify an IP and a name'
    try:
      socket.inet_aton(args[1])
    except:
      return 'First argument must be a valid IPv4 address'
    bot.host_names[args[1]] = args[2]
    conn = (0 if connected(args[1]) else 3)
    bot.host_pings[args[1]] = conn
    update(bot,args[2],'-+'[conn==0])
    return 'Added watch'

  elif args[0]=='remove':
    if len(args)<2:
      return 'You must specify an IP to remove'
    if args[1] not in bot.host_names.keys():
      return 'Unknown IP'
    ip = args[1]
    name = bot.host_names[ip]
    del bot.host_names[ip]
    del bot.host_pings[ip]
    if name not in bot.host_names.values():
      del bot.host_pending[name]
      try:
        del bot.host_tracker.matrix[name]
      except KeyError:
        pass
      bot.host_tracker.save(WATCHFILE)

    return 'Removed watch'

@botidle(freq=60,thread=True)
def idle(bot):

  if not connected(ROUTER):
    return

  for (host,name) in bot.host_names.items():
    msg = None
    online = connected(host)
    if host in bot.host_pings:
      if online:
        if bot.host_pings[host]>=3:
          msg = '[ + ] %s (%s)' % (name,host)
        bot.host_pings[host] = 0
      else:
        if bot.host_pings[host]==2:
          msg = '[ - ] %s (%s)' % (name,host)
        bot.host_pings[host] = min(bot.host_pings[host]+1,3)
    else:
      bot.host_pings[host] = (0 if online else 3)

    if msg:
      if bot.opt('watch.notify'):
        to = bot.get_protocol('xmpp').new_room('watch@conference.area11.jahschwa.com')
        bot.send(msg,to)

      update(bot,name,'-+'['+' in msg])

def update(bot,name,status):
  if os.path.isfile(WATCHFILE):
    bot.host_tracker.load(WATCHFILE)
  bot.host_tracker.update(time.time(),name,status)
  bot.host_tracker.save(WATCHFILE)

def connected(ip):
  cmd = ['arping','-c','10','-f',ip]
  p = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  (stdout,stderr) = p.communicate()
  return (not stderr) and ('Received 0 response' not in stdout)

