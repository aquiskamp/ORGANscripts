#test time
import time
from datetime import datetime
from pytz import timezone

fmt = "%Y_%m_%d{}%H_%M_%S"
tz = ['Australia/Perth']

t = datetime.now(timezone('Australia/Perth')).strftime(fmt)

print(t)

