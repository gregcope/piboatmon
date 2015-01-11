class piboatmon::overclock {

  # put config file in
  # restart service
  file { '/boot/config.txt':
    owner => root,
    group => root,
    ensure => file,
    source => '/tmp/piboatmon/manifests/config.txt',
    # special contents
    #arm_freq=900
    #
    #gpu_mem=16
    #core_freq=250
    #sdram_freq=450
    #over_voltage=2
  }
}
