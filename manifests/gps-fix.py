import gps

# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
lat = 0
lon = 0
# track in gps land
heading = 0
speed = 0

while True:
    try:
    	report = session.next()
        if report['class'] == 'TPV':
            # print report
            if hasattr(report, 'speed'):
                speed = report.speed
            if hasattr(report, 'track'):
                heading = report.track
            if hasattr(report, 'lat'):
                lat = report.lat
            if hasattr(report, 'lon'):
                lon = report.lon
            break
    except KeyError:
		pass
    except KeyboardInterrupt:
		quit()
    except StopIteration:
		session = None
		print "GPSD has terminated"

print 'Speed:', speed
print 'lat: ', lat
print 'lon: ', lon
print 'heading: ', heading 
