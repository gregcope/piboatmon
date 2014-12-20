class piboatmon::logrotate {

  # enabled logcompression
  file { '/etc/logrotate.d/compress':
    ensure => present,
    mode => '0644',
    content => 'compress'
  }
}
