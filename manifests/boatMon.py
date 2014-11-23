import gps



# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

while True:
    try:
    	report = session.query(os)
		# Wait for a 'TPV' report and display the current time
		# To see all report data, uncomment the line below
		# print report
        if report['class'] == 'TPV':
            if hasattr(report, 'latitude'):
                print 'lat is: ', report.latitude
            if hasattr(report, 'long'):
                print 'lon is: ', report.longitude
            if hasattr(report, 'heading'):
                print 'heading is: ', report.eph
    except KeyError:
		pass
    except KeyboardInterrupt:
		quit()
    except StopIteration:
		session = None
		print "GPSD has terminated"
