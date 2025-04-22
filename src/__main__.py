import sys
import os
from run import app_run
# init project structure
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

if __name__=='__main__':
    app_run()
