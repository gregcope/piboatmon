class piboatmon::gpsdate {

  # service to ensure the right rc links go in
  service { 'gpsdate':
    ensure => false,
    enabled => true,
    require => File [ '/etc/init.d/gpsdate' ],
  }


  # put the start script in
  # call the service
  file { '/etc/init.d/gpsdate':
    owner => root,
    group => root,
    ensure => file,
    source => '/home/pi/piboatmon/manifests/gpsdate',
    notify => Service [ 'gpsdate' ],
  }
}
