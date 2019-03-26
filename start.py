from mydsl import dsl_core, dsl_mongo, dsl_server
import yaml
import os

print(dsl_mongo.loadDslFunctions)
dsl_mongo.loadDslFunctions(dsl_core.dslFunctions)
dsl_server.loadDslFunctions(dsl_core.dslFunctions, dsl_core.dslAvailableFunctions)

with open('router.yml') as yaml_file:
  dsl = yaml.load(yaml_file)
  router, err = dsl_core.Argument(dsl).evaluate({"port": int(os.environ.get('PORT', 0))})
