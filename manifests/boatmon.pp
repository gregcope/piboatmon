# class to install / configure gps on rpi UART port

class rpi::boatmon {

  # add a logrotate
  file { '/etc/logrotate.d/boatmon':
    ensure => present,
    content => "/home/pi/rpi/files/boatmon.log {\n\tweekly\n\trotate 31\n\tmissingok\n\tnotifempty\n\tcompress\n\tnocreate\n}\n",
  }
}
