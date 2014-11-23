
# stolen from speedtest-cli
# https://github.com/sivel/speedtest-cli

import math

# lat:  51.013653333
# lon:  -0.449591667

distance

def distance(origin, destination):
    """Determine distance between 2 sets of [lat,lon] in km"""
 
     lat1, lon1 = origin
     lat2, lon2 = destination
     radius = 6371  # km
 
     dlat = math.radians(lat2 - lat1)
     dlon = math.radians(lon2 - lon1)
     a = (math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat    1))
          * math.cos(math.radians(lat2)) * math.sin(dlon / 2)
          * math.sin(dlon / 2))
     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
     d = radius * c

     return d
