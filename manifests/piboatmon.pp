class piboatmon::boatmon {

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

}
