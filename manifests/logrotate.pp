class piboatmon::logrotate {

  # add a logrotate
  file { '/etc/logrotate.d/boatmon':
    ensure => present,
    content => "/home/pi/piboatmon/files/boatmon.log {\n\tweekly\n\trotate 31\n\tmissingok\n\tnotifempty\n\tcompress\n\tnocreate\n}\n",
  }

  # enabled logcompression
  file { '/etc/logrotate.d/compress':
    ensure => present,
    mode => '0644',
    content => 'compress'
  }
}
