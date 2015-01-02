# class to install / configure gps on piboatmon UART port

class piboatmon::gps {

# install some sensible packages
  package { 'gpsd': ensure => installed }
  package { 'gpsd-clients': ensure => installed }
  package { 'pps-tools': ensure => installed }

# fire up gpsd
# if we have the package and the config and the UART is no longer a serial console
  service { 'gpsd':
    ensure => running,
    hasstatus => true,
    hasrestart => true,
    require => [ Package['gpsd'], File ['/etc/default/gpsd'], Exec [ 'removeTtyAMOinittab' ], Exec [ 'removeTtyBootCmdline' ] ],
  }
  
# tweak config to use UART and sock
  file { '/etc/default/gpsd':
    ensure => present,
    content => "START_DAEMON=\"true\"\nGPSD_OPTIONS=\"-n -D 2\"\nDEVICES=\"/dev/ttyAMA0\"\nUSBAUTO=\"true\"\nGPSD_SOCKET=\"/var/run/gpsd.sock\"\n",
  }

# add the pps-gpio module to the end of /etc/modules
# if not present

  exec { 'addPpsGpioEtcModules':
    logoutput => true,
    command => '/bin/echo "pps-gpio" >> /etc/modules',
    unless => '/bin/grep "pps-gpio" /etc/modules',
  }

# remove the UART console
# unless already gone
  exec { 'removeTtyAMOinittab':
    logoutput => true,
    command => '/usr/bin/perl -p -i -e "s#T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100#\#T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100#" /etc/inittab',
    unless => '/bin/grep "#T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100" /etc/inittab',
  }

# remove UART console
# onlyif there
  exec { 'removeTtyBootCmdline':
    logoutput => true,
    command => '/usr/bin/perl -p -i -e "s/console=ttyAMA0,115200//" /boot/cmdline.txt',
    onlyif => '/bin/grep "console=ttyAMA0,115200" /boot/cmdline.txt',
  }

# Add PPS to GPIO 23
  exec { 'addPpsGPIOToBootCmdline':
    logoutput => true,
    command => '/usr/bin/perl -p -i -e "s/rootwait/bcm2708\.pps_gpio_pin=23 rootwait/" /boot/cmdline.txt',
#    unless => '/bin/grep "bcm2708.pps_gpio_pin=23 rootwait" /boot/cmdline.txt',
  }

}
