import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import sys
import os.path
#import pyomo
import pyomo.environ as pyo
#import pvlib
#import math
#from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
import time
from pyomo.environ import *
import sys,os
sys.path.append(os.getcwd())
import random
import os
from datetime import datetime
import logging
import traceback
from shutil import copyfile
import multiprocessing
#import cloudpickle
from pyomo.common.tempfiles import TempfileManager
import forecasters


class Forecasting():

    