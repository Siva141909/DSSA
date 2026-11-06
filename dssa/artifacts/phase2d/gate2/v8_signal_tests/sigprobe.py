import sys, json; sys.path.insert(0, "/Users/siva/Documents/Major project/dssa/phase2d")
import sigsafe
before = sigsafe.report(); sigsafe.restore(); after = sigsafe.report()
print(json.dumps({"label": sys.argv[1], "before_restore": before, "after_restore": after}))
