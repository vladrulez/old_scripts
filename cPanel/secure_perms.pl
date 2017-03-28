#! /usr/bin/perl

###########################
# version 0.2 31/08/2012
# Correct default cPanel permissions
# Author: Vladimir Blokhin
###########################

my $stri = '';
my $stru = '';

system("/bin/chmod 711 /etc/valiases 2> /dev/null");
system("/bin/chmod 711 /etc/vdomainaliases 2> /dev/null");
system("/bin/chmod 711 /etc/vfilters 2> /dev/null");
system("/bin/chmod 751 /etc/vmail 2> /dev/null");
system("/bin/chmod 640 /etc/named.conf 2> /dev/null");
system("/bin/chmod 600 /root/.ssh");
system("/bin/chmod 600 /root/.ssh/authorized_keys");
system("/bin/chmod 700 /usr/local/etc/scripts");
system("/bin/chmod 711 /home");
system("test -e /home2 && /bin/chmod 711 /home2");
system("test -e /usr/local/bin/mc && /bin/chmod 750 /usr/local/bin/mc  > /dev/null");
system("test -e /usr/bin/mc && /bin/chmod 750 /usr/bin/mc > /dev/null");
system("/bin/chmod 750 /usr/bin/gcc");

my @php_ini_files = ('/usr/php4/lib/php.ini', '/usr/lib/php.ini', '/usr/local/lib/php.ini', '/opt/php52/lib/php.ini', '/opt/php53/lib/php.ini');
my $disable_mask = 's/^\s*disable_functions\s*=.*$/disable_functions = show_source,symlink,shell_exec,exec,proc_close,proc_open,popen,system,dl,passthru,escapeshellarg,escapeshellcmd/g';
foreach my $file (@php_ini_files)
{
   system("test -e $file && perl -i -pe \'$disable_mask\' $file");
}

my @acc_names = ();
@acc_names = `grep /bin/bash /etc/passwd|awk -F: '{print \$1}'`;

foreach my $acc_name ( @acc_names )
{
   chomp $acc_name;
   my $acc_test_name = `grep -w -h $acc_name /etc/trueuserdomains|awk '{print \$2}'`;
   chomp $acc_test_name;
   if ( $acc_name eq $acc_test_name ) { system("chsh -s /usr/local/cpanel/bin/jailshell $acc_name"); }
}

@acc_names = ();
open(FF, "grep :/home /etc/passwd|/usr/bin/awk -F: \'{print \$6}\'|");
while(<FF>)
{
   chomp $_;
   push(@acc_names,$_);
}
close(FF);

my $acc_index = $#acc_names;
my $ii = 0; my $i = 0; my $acc_end = 0;
my $exec_status = ''; my $stri2 = ''; my $stru2 = '';

while ( $ii < $acc_index )
{
   $acc_end = $ii + 100;
   if ( $acc_end > $acc_index ) { $acc_end = $acc_index; }
   for ($i = $ii; $i < $acc_end; $i++)
   {
      $stri = $stri . ' ' . $acc_names[$i];
      $stru = $stru . ' ' . $acc_names[$i] . '/public_html';
   }
   $exec_status = system("/bin/chmod 711 $stri 2> /dev/null");
   if ( $exec_status != 0 )
   {
      for ($i = $ii; $i < $acc_end; $i++) { $stri2 = $acc_names[$i]; system("/bin/chmod 711 $stri2 2> /dev/null"); }
   }
   $exec_status = system("/bin/chmod 750 $stru 2> /dev/null");
   if ( $exec_status != 0 )
   {
      for ($i = $ii; $i < $acc_end; $i++) { $stru2 = $acc_names[$i]."/public_html"; system("/bin/chmod 750 $stru2 2> /dev/null"); }
   }
   $exec_status = system("/bin/chown :nobody $stru 2> /dev/null");
   if ( $exec_status != 0 )
   {
      for ($i = $ii; $i < $acc_end; $i++) { $stru2 = $acc_names[$i]."/public_html"; system("/bin/chown :nobody $stru2 2> /dev/null"); }
   }
   $ii = $acc_end; $stri = ''; $stru = '';
}