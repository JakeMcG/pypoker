import utils.bcp as bcp
import sys

if sys.argv[1] == "hand":
    bcp.handToJsonFile(sys.argv[2])
