class piboatmon::mopi {

  simbamond_sha=5f6075294299c0b4e405081778f307c389c17ddd

  # install some sensible packages
  package { 'simbamond': ensure => installed }

  # fire up simbamond
  # require package to be installed and config file, 
  service { 'simbamond':
    ensure => running,
    hasstatus => true,
    hasrestart => true,
    require => [ Package['simbamond'], File [ '/etc/default/simbamond' ] ],
  }

  # put config file in
  # restart service
  file { '/etc/default/simbamond':
    owner => root,
    group => root,
    ensure => file,
    source => '/tmp/piboatmon/manifests/simbamond',
    notify => Service [ 'simbamond' ],
    #
    # special contents
    # # wc1: -wc1 1 15000 12500 11000 11000
    # # wc2: -wc2 2 9600 7400 5200 4800
    # /usr/sbin/mopicli -wc2 2 9600 7400 5200 4800
    # /usr/sbin/mopicli -wc1 1 15000 12500 11000 11000
  }
}
