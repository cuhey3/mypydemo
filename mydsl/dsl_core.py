import re
import asyncio
import threading
import time
import yaml
loop = asyncio.get_event_loop()

dslFunctions = {}
dollerReplacePattern = re.compile(r'^(\$\.?)')
firstValuePattern = re.compile(r'^([^\[ \]\.]+)\.?(.+)$')
nextKeyPattern = re.compile(r'^(\[([^\[\]]+)\]|([^\[\] \.]+))\.?(.*)$')
dslAvailableFunctions = {}

def evaluateAll(args, container):
    result = []
    for arg in args:
        evaluated, err = arg.evaluate(container)
        if err != None:
            return None, err
        else:
            result.append(evaluated)
    return result, None


def propertyGet(parent, key):
    # print("propertyGet",parent, key, type(parent), type(key))
    keyType = type(key)
    if keyType == str:
        try:
            numKey = int(key)
            return parent[numKey], None
        except:
            if hasattr(parent, key):
                return getattr(parent, key), None
            else:
                if isinstance(parent, dict):
                    return parent[key], None
    elif keyType == int:
        return parent[key], None
    else:
        return None, Exception("propertyGet error: key type is invalid.")


def getLastKeyValue(container, arg, root=None):
    rawArg = arg.rawArg()
    rootIsNone = root == None
    if rootIsNone:
        root = container
    rawArgType = type(rawArg)
    if rawArgType == str:
        if rawArg == "$":
            return ["", root], None
        elif rawArg in dslAvailableFunctions:
            return ["", dslAvailableFunctions[rawArg]], None
        elif "." not in rawArg and "[" not in rawArg:
            return ["", rawArg], None
        else:
            cursor = container
            remainStr = rawArg
            if rootIsNone:
                firstValueMatch = firstValuePattern.match(remainStr)
                lastKeyValue, err = getLastKeyValue(
                    container, Argument(firstValueMatch.group(1)))
                if err != None:
                    return None, err
                firstValue = lastKeyValue[1]
                if firstValue != None:
                    cursor = firstValue
                    remainStr = firstValueMatch.group(2)
                else:
                    return [None, rawArg], None
            while True:
                nextKeyMatch = nextKeyPattern.match(remainStr)
                if nextKeyMatch:
                    arrayKeyStr = nextKeyMatch.group(2)
                    periodKeyStr = nextKeyMatch.group(3)
                    remain = nextKeyMatch.group(4)
                    if periodKeyStr:
                        if arrayKeyStr:
                            nextKeyResult, err = getLastKeyValue(
                                root, Argument(arrayKeyStr))
                            if err != None:
                                return None, err
                        else:
                            nextKeyResult, err = getLastKeyValue(
                                root, Argument(periodKeyStr))
                            if err != None:
                                return None, err
                        if nextKeyResult[0] == "":
                            nextKey = nextKeyResult[1]
                        elif nextKeyResult[0] == None:
                            nextKey = None
                        else:
                            result, _ = propertyGet(nextKeyResult[1],
                                                    nextKeyResult[0])
                            nextKey = result
                    else:
                        evaluated, err = Argument(arrayKeyStr).evaluate(
                            container)
                        if err == None:
                            nextKey = evaluated
                        else:
                            return None, err
                    if remain == "":
                        return [nextKey, cursor], None
                    else:
                        result, err = propertyGet(cursor, nextKey)
                        if err == None:
                            cursor = result
                        else:
                            return None, err
                        remainStr = remain
                else:
                    return [None, None], None
    else:
        evaluated, err = arg.evaluate(container)
        if err == None:
            return ["", evaluated], None
        else:
            return None, err


def _print(container, *args):
    result, err = evaluateAll(args, container)
    if err != None:
        return None, err
    print(*result)
    return None, None


def _get(container, *args):
    firstArg, args = args[0], args[1:]
    lastKeyValue, err = getLastKeyValue(container, firstArg, None)
    if err != None:
        return None, err
    key = lastKeyValue[0]
    parentValue = lastKeyValue[1]

    # get default value
    defaultValue = None
    if len(args) > 0:
        if type(args[len(args) - 1].rawArg()) != str:
            lastArg, args = args[len(args) - 1], args[:len(args) - 1]
            evaluated, err = lastArg.evaluate(container)
            if err != None:
                return None, err
            defaultValue = evaluated
    if parentValue != None:
        if key == None:
            return parentValue, None
        else:
            if key == "":
                cursor = parentValue
            else:
                keyType = type(key)
                if keyType == str:
                    try:
                        numKey = int(key)
                        cursor = parentValue[numKey]
                    except Exception as e:
                        # print(e)
                        cursor = parentValue.get(key, None)
                elif keyType == int:
                    cursor = parentValue[key]
            while len(args) > 0:
                shiftArg, args = args[0], args[1:]
                key, err = shiftArg.evaluate(container)
                if err != None:
                    return None, err
                cursor = cursor[key]
            if cursor == None and len(args) == 0:
                return defaultValue, None
            return cursor, None


def _set(container, *args):
    evaluated, err = args[1].evaluate(container)
    if err != None:
        return None, err
    lastKeyValue, err = getLastKeyValue(container, args[0])
    if err != None:
        return None, err
    key = lastKeyValue[0]
    parentValue = lastKeyValue[1]
    if parentValue != None and key != None and key != "":
        keyType = type(key)
        if keyType == str:
            try:
                numKey = int(key)
                parentValue[numKey] = evaluated
            except:
                parentValue[key] = evaluated
        elif keyType == int:
            parentValue[key] = evaluated
    return None, None


def _function(container, *args):
    _funcContainer = container
    fixedArguments = {}
    argumentNames = args[0].rawArg()
    process = args[1]
    if len(args) > 2:
        for fixedKey in args[2].rawArg():
            evaluated, err = Argument("$." + fixedKey).evaluate(container)
            if err != None:
                return None, err
            fixedArguments[fixedKey] = evaluated

    def func(*_args):
        for i, argumentName in enumerate(argumentNames):
            _funcContainer[argumentName] = _args[i]
        _funcContainer["this"] = container
        for k, v in fixedArguments.items():
            _funcContainer[k] = v
        result, err = process.evaluate(_funcContainer)
        if err != None:
            return err
        if "exit" in _funcContainer:
            del _funcContainer["exit"]
        if "this" in _funcContainer:
            del _funcContainer["this"]
        return result

    return func, None


def _do(container, *args):
    firstArg, args = args[0], args[1:]
    lastKeyValue, err = getLastKeyValue(container, firstArg, None)
    if err != None:
        return None, err
    key = lastKeyValue[0]
    parentValue = lastKeyValue[1]
    if parentValue == None or key == None:
        return None, None
    cursor = None
    if key == "":
        cursor = parentValue
    else:
        result, _ = propertyGet(parentValue, key)
        cursor = result
    while not callable(cursor) and len(args) > 0:
        nextArg, args = args[0], args[1:]
        key, err = nextArg.evaluate(container)
        if err != None:
            return None, err
        cursor, _ = propertyGet(cursor, key)
        if cursor == None:
            break

    if callable(cursor):
        evaluated, err = evaluateAll(args, container)
        if err != None:
            return None, err
        if len(evaluated) == 1 and isinstance(evaluated[0], dict):
            return cursor(**evaluated[0]), None
        else:
            return cursor(*evaluated), None
    else:
        return None, None

def _sequence(container, *args):
    if not "seqArray" in container:
        container["seqArray"] = []
    seqIndex = len(container["seqArray"])
    for arg in args:
        evaluated, err = arg.evaluate(container)
        print("sequence", evaluated, err)
        if err != None:
            return None, err
        if evaluated != None:
            container["seq"] = evaluated
            if len(container["seqArray"]) == seqIndex:
                container["seqArray"].append(None)
            container["seqArray"][seqIndex] = evaluated
        if "exit" in container and container["exit"] == True:
            break
    container["seqArray"] = container["seqArray"][0:seqIndex]
    return container.get("seq"), None

task = None
def _asyncTest(container, *args):
  async def sleeper(i):
    await asyncio.sleep(i)
  async def waiter():
    while True:
      await sleeper(1)
      print("foo")
  global task;
  task = loop.create_task(waiter())
  return task, None

def _stopTest(container, *args):
  global task;
  task.cancel()
  return None, None

def _now(container, *args):
  return int(time.time()*1000), None

def _format(container, *args):
	formatString = args[0].rawArg()
	args = args[1:]
	for arg in args:
		evaluated, err = arg.evaluate(container)
		if err != None :
			return None, err
		formatString = formatString.replace("%s", str(evaluated), 1)
	return formatString, None

def _parseYaml(container, *args):
	evaluated, err = args[0].evaluate(container)
	if err != None:
		return None, err
	return yaml.load(evaluated), None

def _filter(container, *args):
  _self = container
  toFilter, err = args[0].evaluate(container)
  if err != None :
  	return None, err
  key = "item"
  if len(args) > 2 :
  	key = args[2].rawArg()
  result = []
  toFilterSize = len(toFilter)
  for index, value in enumerate(toFilter) :
  	_self[key] = value
  	_self["index"] = index
  	evaluated, err = args[1].evaluate(_self)
  	if err != None :
  		return None, err
  	if evaluated == True :
  		result.append(value)
  	if toFilterSize -1 == index :
  		del _self[key]
  		del _self["index"]
  return result, None

def _is(container, *args):
	leftValueEvaluated, err = args[0].evaluate(container)
	if err != None :
		return None, err
	rightValueEvaluated, err = args[1].evaluate(container)
	if err != None :
		return None, err
	print("compare...", leftValueEvaluated, rightValueEvaluated, type(leftValueEvaluated), type(rightValueEvaluated))
	return leftValueEvaluated == rightValueEvaluated, None

def _not(container, *args):
  delegated, err = _is(container, *args)
  if err != None :
  	return None, err  
  return not delegated, None

def _when(container, *args):
  while len(args) > 0 :
  	evaluated, err = args[0].evaluate(container)
  	if err != None :
  		return None, err
  	if not isinstance(evaluated, bool):
  		return None, Exception("{}: {} is not bool type.".format(args[0].rawArg(), evaluated))
  	else:
  		if evaluated == True :
  			sequence, err = args[1].evaluate(container)
  			if err == None :
  				return sequence, None
  			else:
  				return None, err
  		else:
  			args = args[2:]
  return None, Exception("DslFunctions.when: no match ({})".format(args))

def _len(container, *args):
	evaluated, err = args[0].evaluate(container)
	if err != None :
		return None, err
	return len(evaluated), None

def _str(container, *args):
	evaluated, err = args[0].evaluate(container)
	if err != None :
		return None, err
	return str(evaluated), None

dslFunctions["print"] = _print
dslFunctions["get"] = _get
dslFunctions["set"] = _set
dslFunctions["function"] = _function
dslFunctions["do"] = _do
dslFunctions["sequence"] = _sequence
dslFunctions["asyncTest"] = _asyncTest
dslFunctions["stopTest"] = _stopTest
dslFunctions["now"] = _now
dslFunctions["format"] = _format
dslFunctions["parseYaml"] = _parseYaml
dslFunctions["filter"] = _filter
dslFunctions["is"] = _is
dslFunctions["not"] = _not
dslFunctions["when"] = _when
dslFunctions["len"] = _len
dslFunctions["str"] = _str

class Argument():
    __rawArg = None

    def __init__(self, rawArg):
        if type(rawArg) is str and rawArg != "$":
            self.__rawArg = dollerReplacePattern.sub(r'$.', rawArg)
        else:
            self.__rawArg = rawArg

    def rawArg(self):
        return self.__rawArg

    def evaluate(self, container):
        print("evalaute start", self.__rawArg)
        t = type(self.__rawArg)
        if t is str:
            if self.__rawArg == "$":
                return container, None
            elif self.__rawArg.startswith("$"):
                return dslFunctions["get"](container, Argument(self.__rawArg))
            else:
                return self.__rawArg, None
        elif isinstance(self.__rawArg, list):
            result = []
            for arg in self.__rawArg:
                print(arg)
                evaluatedValue, err = Argument(arg).evaluate(container)
                if err != None:
                    return None, err
                else:
                    result.append(evaluatedValue)
            return result, None
        elif isinstance(self.__rawArg, dict):
            dict_len = len(self.__rawArg)
            if dict_len == 0:
                return {}, None
            elif dict_len == 1:
                firstKey = list(self.__rawArg.keys())[0]
                if firstKey in dslFunctions:
                    wrappedArgs = []
                    value = self.__rawArg[firstKey]
                    if isinstance(value, list):
                        wrappedArgs.extend(self.__rawArg[firstKey])
                    else:
                        wrappedArgs.append(value)
                    wrappedArgs = map(lambda arg: Argument(arg), wrappedArgs)
                    return dslFunctions[firstKey](container, *wrappedArgs)
                elif firstKey.startswith("$"):
                    return dslFunctions["set"](container, Argument(firstKey),
                                               Argument(
                                                   self.__rawArg[firstKey]))
                else:
                  return self.__rawArg, None # TBD
            else:
              evaluatedDict = {}
              for key, value in self.__rawArg.items():
                evaluated, err = Argument(value).evaluate(container)
                if err != None:
                  return None, err
                evaluatedDict[key] = evaluated
              return evaluatedDict, None  # TBD
        else:
            return self.__rawArg, None
