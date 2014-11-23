uptime, idletime = [float(f) for f in open("/proc/uptime").read().split()]
print 'Uptime in secs: ',uptime
