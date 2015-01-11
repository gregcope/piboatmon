class piboatmon::overclock {

  # put config file in
  # restart service
  file { '/boot/config.txt':
    owner => root,
    group => root,
    ensure => file,
    mode => '0755',
    source => '/tmp/piboatmon/manifests/config.txt',
    require => Exec [ 'bootrw' ],
    # special contents
    #arm_freq=900
    #
    #gpu_mem=16
    #core_freq=250
    #sdram_freq=450
    #over_voltage=2
  }

  exec { 'bootrw':
    logoutput => true,
    command => '/bin/mount -o remount,rw /boot',
    unless => '/bin/mount | /bin/grep boot | /bin/grep rw',
  }
}
