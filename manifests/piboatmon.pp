# class to install / configure gps on rpi UART port

class rpi::boatmon {

  # add a logrotate
  file { '/etc/logrotate.d/boatmon':
    ensure => present,
    content => "/home/pi/rpi/files/boatmon.log {\n\tweekly\n\trotate 31\n\tmissingok\n\tnotifempty\n\tcompress\n\tnocreate\n}\n",
  }

  # install git
  package { 'git': ensure => installed }

  # this downloads HEAD which is not what we want
  # but should work fine...
  exec { 'gitClonePiBoatMon':
    logoutput => true,
    cwd => '/home/pi',
    user => 'pi',
    group => 'pi',
    command => '/usr/bin/git https://github.com/gregcope/piBoatMon.git'
    unless => 'ls /home/pi/piBoatMon'
  }
}
