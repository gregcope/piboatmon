class piboatmon::piboatmon {

  # install git
  package { 'git': ensure => installed }

  # this downloads HEAD which is not what we want
  # but should work fine...
  exec { 'gitClonePiBoatMon':
    logoutput => true,
    cwd => '/home/pi',
    user => 'pi',
    group => 'pi',
    command => '/usr/bin/git https://github.com/gregcope/piboatmon.git',
    unless => '/bin/ls /home/pi/piboatmon',
  }

  # put config file in
  # restart service
  file { '/etc/rc.local':
    owner => root,
    group => root,
    ensure => file,
    mode => '0755',
    source => '/home/pi/piboatmon/manifests/rc.local',
  }

  # add a logrotate for piboatmon
#  file { '/etc/logrotate.d/boatmon':
#    ensure => present,
#    content => "/home/pi/piboatmon/files/piboatmon.log\n/home/pi/piboatmon/files/gpspipe.log {\n\tdaily\n\trotate 31\n\tmissingok\n\tnotifempty\n\tcompress\n\tnocreate\n}\n",
#  }

}
