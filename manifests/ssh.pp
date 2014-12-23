# class to install my ssh key!!!

class piboatmon::ssh {

  file { '/home/pi/.ssh/authorized_keys':
    ensure => present,
    owner => 'pi',
    group => 'pi',
    mode => '0600',
    content => "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCmhxPXUWgdEy5dGVEn6lwCI07Zd5GNPT14Yd7GfsAOeYHP9q4prEPrH2eboyUCMU8NSJ8UL0rOSdQhmikgCz1Vdw3mC8IDp1WXyd08DLwG/4WhuYLG0gs72Izg9CO397AZ/XvQ9ed42kLdqHKgCrbcixt9lRoBAmSVBmBQpciSPyFJ5Hv2M5ifYxxKBvQYi5lrEkWvrIHpS46V4oDc2Ko6TIIQbTubk0Yq8phj6h3UpQQqGMRJ2kfKuL1VInqD5jIzNqYTOUe+OjMZOFbqr5yP4rzNVAZZ5DYeprDNfefpmCQhK1rQGAUMYO0IhNKPA0QY2sT/98310BqnzqiyJMsV",
  }

}
