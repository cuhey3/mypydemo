import pymongo
import os
from urllib.parse import urlparse

class __MongoUtil():
  def __init__(self):
    self.mongodbUri = os.environ.get('MONGODB_URI')
    if not self.mongodbUri:
      raise Exception()
    self.client = pymongo.MongoClient(self.mongodbUri)
    self.dbname = urlparse(self.mongodbUri).path[1:]
  def collection(self, collectionName):
      return self.client[self.dbname][collectionName]

    
__sharedInstance = __MongoUtil()

def mongoUtil():
  return __sharedInstance

def loadDslFunctions(dslFunctions):
  def mongoGet(container, *args):
    collectionName = args[0].rawArg()
    # print("collectionName", collectionName)
    collection = mongoUtil().collection(collectionName)
    try:
      result = list(collection.find())
      return result, None
    except Exception as e:
      return None, e
  
  dslFunctions["mongoGet"] = mongoGet
  
  def mongoInsert(container, *args):
    collectionName = args[0].rawArg()
    obj, err = args[1].evaluate(container)
    if err != None :
      return None, err
      
    collection = mongoUtil().collection(collectionName)
    try:
      res = collection.insert_one(obj)
      return res, None
    except Exception as e:
      return None, e

  dslFunctions["mongoInsert"] = mongoInsert
  
  def mongoReplace(container, *args):
    collectionName = args[0].rawArg()
    obj, err = args[1].evaluate(container)
    if err != None:
      return None, err

    collection = mongoUtil().collection(collectionName)
    res = collection.replace_one({"_id": obj["_id"]}, obj)
    return res, None

  dslFunctions["mongoReplace"] = mongoReplace
