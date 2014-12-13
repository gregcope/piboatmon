class piboatmon::puppet {

  # remove the puppet start links
  # so that we do not even try to start it
  service { 'puppet':
    enable => false,
  }

}
