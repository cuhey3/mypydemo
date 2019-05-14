import os
from jinja2 import FileSystemLoader, Environment
import aiohttp
import asyncio
import time
import re
import json
from mydsl.dsl_core import Argument
from aiohttp import web
loop = asyncio.get_event_loop()

templateLoader = FileSystemLoader(searchpath="./templates")
templateEnv = Environment(loader=templateLoader)

def nl2brAndNbsp(content):
  return content.replace("\n", "<br>").replace(" ", "&nbsp;")
  
templateEnv.filters['nl2brAndNbsp'] = nl2brAndNbsp

def _handler(container, *args):
    endpoint = args[1].rawArg()
    viewOrLogic = args[2].rawArg()
    if type(viewOrLogic) == str:
        return None, None  # TBD
    else:
        async def handle(request):
          requestBody = await request.post()
          newContainer = {"req": request, "resp": web.Response, "requestBody": requestBody}
          result, err = args[2].evaluate(newContainer)
          print("hehehe", result, err)
          if err != None:
            raise err
          else:
            return result
        if args[0].rawArg() == "get":
          container["router"].add_routes([web.get(endpoint, handle)])
        else:
          container["router"].add_routes([web.post(endpoint, handle)])
        return None, None


def _render(container, *args):
    evaluated, err = args[0].evaluate(container)
    template = templateEnv.get_template(evaluated)
    templateArgument, err = args[1].evaluate(container)
    if err != None:
        return None, err
    html = template.render(**templateArgument)
    result = container["resp"](text=html, content_type='text/html')
    return result, None

subscribers = {
    
}

def _subscribe(container, *args):
  channelName, err = args[0].evaluate(container)
  if err != None:
    return None, err
  processId = str(time.time())
  channelSubscribers = subscribers.get(channelName,{})
  async def onSubscribeFunc(data):
    newContainer = {"subscribe": data, "channelName": channelName}
    if len(args)> 2:
      for key in args[2].rawArg():
        newContainer[key] = container[key]
    args[1].evaluate(newContainer)
    
  channelSubscribers[processId] = onSubscribeFunc
  subscribers[channelName] = channelSubscribers
  
  def onUnsubscribeFunc():
    del subscribers[channelName][processId]
  return onUnsubscribeFunc, None
  
def _publish(container, *args):
  channelName, err = args[0].evaluate(container)
  if err != None:
    return None, err
  evaluated, err = args[1].evaluate(container)
  if err != None:
    return None, err
  if channelName not in subscribers:
    # return None, Exception("channel: {} has no subscribers.".format(channelName))
    subscribers[channelName] = {}
    return None, None
  for _, func in subscribers[channelName].items():
    loop.create_task(func(evaluated))
  return None, None

def _timer(container, *args):
  interval, err = args[0].evaluate(container)
  if err != None:
    return None, err
  async def sleeper():
    await asyncio.sleep(interval)
  async def waiter():
    while True:
      await sleeper()
      args[1].evaluate(container)
  task = loop.create_task(waiter())
  def onStopFunc():
    task.cancel()
  return onStopFunc, None

processes = {}

def _processStart(container, *args):
  processId, err = args[0].evaluate(container)
  if err != None:
    return None, err
  else:
    print("process start", processId)
    dsl, err = args[1].evaluate(container)
    if err != None:
      return None, err
    result, err= Argument(dsl).evaluate(container)
    if err != None:
      return None, err
    processes[processId] = result
    return None, None

def _processKill(container, *args):
  processId, err = args[0].evaluate(container)
  if err != None:
    return None, err
  else:
    if processId in processes:
      processes[processId]()
      del processes[processId]
    return None, None

def _redirect(container, *args):
  toRedirect = args[0].rawArg()
  return None, aiohttp.web.HTTPFound(toRedirect)

processIdPattern = re.compile(r'(.+)(\d{13})$')

def _processes(container, *args):
  result = {}
  for key, _ in processes.items():
    match = processIdPattern.match(key)
    yamlId = match.group(1)
    if yamlId in result:
      result[yamlId].append(match.group(2))
    else:
      result[yamlId] = [match.group(2)]
  return result, None

def _wsHandler(container, *args):
  router = container["router"]
  async def _asyncHandler(request):
    print('Websocket connection starting')
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    print('Websocket connection ready')
    newContainer = {"conn": ws}
    async for msg in ws:
      print(msg)
      if msg.type == aiohttp.WSMsgType.TEXT:
        print(msg.data)
        if msg.data == 'close':
          await ws.close()
          args[2].evaluate(newContainer)
        else:
          newContainer["message"] = json.loads(msg.data)
          args[1].evaluate(newContainer)
          # await ws.send_str(msg.data + '/answer')

    print('Websocket connection closed')
    return ws
  endpoint, err = args[0].evaluate(container)
  if err != None:
    return None, err
  router.router.add_route('GET', endpoint, _asyncHandler)
  return None, None

def _wsWrite(container, *args):
  conn = container["conn"]
  evaluated, err = args[0].evaluate(container)
  if err != None:
    return None, err
  loop.create_task(conn.send_str(json.dumps(evaluated)))
  return None, None

def _channelList(container, *args):
  return list(subscribers.keys()), None

def loadDslFunctions(dslFunctions, dslAvailableFunctions):
  dslFunctions["handler"]      = _handler
  dslFunctions["render"]       = _render
  dslFunctions["redirect"]       = _redirect
  dslFunctions["subscribe"]    = _subscribe
  dslFunctions["publish"]      = _publish
  dslFunctions["timer"]        = _timer
  dslFunctions["processStart"] = _processStart
  dslFunctions["processKill"] = _processKill
  dslFunctions["processes"] = _processes
  dslFunctions["wsHandler"] = _wsHandler
  dslFunctions["wsWrite"] = _wsWrite
  dslFunctions["channelList"] = _channelList
  dslAvailableFunctions["web"] = web
