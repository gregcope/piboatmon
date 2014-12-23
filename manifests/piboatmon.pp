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

# sudo parted /dev/mmcblk0
# mkpart primary 3277 6300
# unless a third partion exists ...
  exec { 'mkDataPart':
    logout => true,
    command => '/sbin/parted /dev/mmcblk0 mkpart primary 3277 630',
    unless => '/sbin/parted /dev/mmcblk0 p | /bin/grep "^ 3"',
  }

  exec { 'createFsOn3Partion':
    logout => true,
    command => '/sbin/mkfs.ext4 /dev/mmcblk0p3',
    unless => '/usr/bin/file -sL /dev/mmcblk0p3  | /bin/grep ext4',
    require => Exec [ 'mkDataPart' ],
  }

  mount { '/piboatmon':
    ensure => present,
    device => '/dev/mmcblk0p3',
    atboot => yes,
    fstype => ext4,
    dump => 0,
    pass => 1,
    options => 'defaults',
    require => Exec [ 'createFsOn3Partion' ],
  }

}
