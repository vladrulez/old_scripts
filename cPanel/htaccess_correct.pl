#!/usr/bin/perl

###########################
# version 0.4 07/11/2011
# .htaccess files converter
# FollowSymLinks issue fix
# Author: Vladimir Blokhin
###########################

use strict;
use Fcntl qw(:DEFAULT :flock);
my $error_log="/usr/local/apache/logs/error_log";
my $message="\n# Options All and FollowSymLinks are disabled on this server.\n# FollowSymLinks is automatically replaced to SymLinksIfOwnerMatch, All is changed heuristically.\n";
open(STDOUT, "|-", "logger -t htaccess_correct.pl") or die("Couldn't open logger output stream: $!\n");
open(STDERR, ">&STDOUT") or die("Couldn't redirect STDERR to STDOUT: $!\n");
$| = 1; chdir('/');
if ( ! -e "$error_log") { print "no $error_log file, exiting \n"; exit;}
my @fileslist=`tail -n 5000 $error_log|grep -i 'not allowed here'|grep -o -e "/home.*/\.htaccess"|sort -u`;
if ( $#fileslist == -1 ) { exit; }
foreach my $i (@fileslist)
 {
 chomp $i;
 if ( -e "$i" )
   {
    my $laststart = &htaccess_conv($i);
    if ( $laststart == 1 ) { print "File $i has been converted \n"; }
    elsif ( $laststart == 2 ) { print "File $i was converted already \n"; }
    else { print "File $i has NOT converted \n"; }
   }
 }
exit;

sub htaccess_conv
{
  my $filename = shift; my @newfile=();
  open(HT,"< $filename") or die "$filename \n";
  flock(HT, LOCK_SH);
  my @oldfile = <HT>;
  foreach my $ii (@oldfile)
   {
    if ( $ii =~ /Options.*(All|FollowSymLinks)/i )
     {
      if ( $ii =~ /^\s*#/ ) { goto internal; }
      else { my $iiold=$ii;
switch:
             if ( $ii =~ /(^\s*Options.*FollowSymLinks)/i ) { $ii =~ s/FollowSymLinks/SymLinksIfOwnerMatch/gi; goto switch;}
	     if ( $ii =~ /(^\s*Options\s*All\s$)/i ) { $ii =~ s/All/SymLinksIfOwnerMatch Indexes Includes/gi; goto endswitch;}
	     if ( $ii =~ /(^\s*Options.*-All)/i ) { $ii =~ s/-All/None/gi; goto endswitch;}
	     if ( $ii =~ /(^\s*Options\s*All\s*.Indexes\s*$)/i ) { $ii =~ s/All/SymLinksIfOwnerMatch Includes/gi; goto endswitch;}
	     if ( $ii =~ /(^\s*Options\s*.Indexes\s*All\s*$)/i ) { $ii =~ s/All/SymLinksIfOwnerMatch Includes/gi; goto endswitch;}
	     if ( $ii =~ /(^\s*Options\s*All\s*.Includes\s*$)/i ) { $ii =~ s/All/SymLinksIfOwnerMatch Indexes/gi; goto endswitch;}
	     if ( $ii =~ /(^\s*Options\s*.Includes\s*All\s*$)/i ) { $ii =~ s/All/SymLinksIfOwnerMatch Indexes/gi; goto endswitch;}
	     if ( $ii =~ /(^\s*Options\s*.Includes\s*All\s*.Indexes\s*$)/i ) { $ii =~ s/All/SymLinksIfOwnerMatch/gi; goto endswitch;}
	     if ( $ii =~ /(^\s*Options\s*.Indexes\s*All\s*.Includes\s*$)/i ) { $ii =~ s/All/SymLinksIfOwnerMatch/gi; goto endswitch;}
	     if ( $ii =~ /(^\s*Options.*\sAll.*$)/i ) { $ii =~ s/All/SymLinksIfOwnerMatch MultiViews Indexes ExecCGI Includes/gi;}
endswitch:
	     push (@newfile,$message);
	   }
    }
internal:	push (@newfile,$ii);
    }
  close(HT);
  if ( @oldfile == @newfile ) { return 2; }
  else {
	 open(HT,"> $filename") or die "$filename \n";
	 flock(HT, LOCK_SH);
	 print (HT @newfile);
	 close(HT);
	 return 1;
	}
}
