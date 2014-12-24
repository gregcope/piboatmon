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
    require => Mount [ '/home/pi' ],
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
    logoutput => true,
    command => '/sbin/parted /dev/mmcblk0 mkpart primary 3277 630',
    unless => '/sbin/parted /dev/mmcblk0 p | /bin/grep "^ 3"',
  }

  exec { 'createFsOn3Partion':
    logoutput => true,
    command => '/sbin/mkfs.ext4 /dev/mmcblk0p3',
    unless => '/usr/bin/file -sL /dev/mmcblk0p3  | /bin/grep ext4',
    require => Exec [ 'mkDataPart' ],
  }

  mount { '/home/pi':
    ensure => mounted,
    device => '/dev/mmcblk0p3',
    atboot => yes,
    fstype => ext4,
    dump => 0,
    pass => 1,
    options => 'defaults',
    require => Exec [ 'createFsOn3Partion' ],
  }

  file { '/home/pi':
    ensure => directory,
    owner => 'pi',
    group => 'pi',
    mode => '0755',
    require => Mount [ '/home/pi' ],
  }

  file { '/home/pi/.ssh':
    ensure => directory,
    owner => 'pi',
    group => 'pi',
    mode => '0600',
    require => [ Mount [ '/home/pi' ], File [ '/home/pi' ] ],
  }

  file { '/home/pi/.ssh/authorized_keys':
    ensure => present,
    owner => 'pi',
    group => 'pi',
    mode => '0600',
    content => "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCmhxPXUWgdEy5dGVEn6lwCI07Zd5GNPT14Yd7GfsAOeYHP9q4prEPrH2eboyUCMU8NSJ8UL0rOSdQhmikgCz1Vdw3mC8IDp1WXyd08DLwG/4WhuYLG0gs72Izg9CO397AZ/XvQ9ed42kLdqHKgCrbcixt9lRoBAmSVBmBQpciSPyFJ5Hv2M5ifYxxKBvQYi5lrEkWvrIHpS46V4oDc2Ko6TIIQbTubk0Yq8phj6h3UpQQqGMRJ2kfKuL1VInqD5jIzNqYTOUe+OjMZOFbqr5yP4rzNVAZZ5DYeprDNfefpmCQhK1rQGAUMYO0IhNKPA0QY2sT/98310BqnzqiyJMsV",
    require => File [ '/home/pi/.ssh' ],
  }
}
