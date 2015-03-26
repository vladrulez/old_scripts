#!/usr/bin/perl
####################################################
# MySQL "general log" parser
# for cPanel servers version 0.2
# Author Vladimir Blokhin
# 01/06/2011
# Usage:
# mysql_log_parse.pl MySQL_log_filename top_length
####################################################
use strict; use Time::Local;
my @CID=(1); my @DBName=("Unknown"); my @MySQLUserName=("Unknown"); my @QueriesNumber=(0);
my @CpanelUserName=("Unknown"); my %currhash = (); my %unknownhash = ();
my %CIDhash = (); my %DBhash = (); my %CpUNhash = (); my %MySQLUNhash = ();
if (! $ARGV[0] ) {print "Usage:\n$0 MySQL_log_filename top_length\n"; exit;}
my $LogFileName = $ARGV[0]; chomp $LogFileName;
my $top_number=10; my $firstdate=""; my $finaldate="";
if ($ARGV[1]) { $top_number=int $ARGV[1]; }
if ( ! -e $LogFileName) { print "no $LogFileName file, exiting\n"; exit;}
my $i=0; my $ii=1;

open LOG, "<".$LogFileName or die "Can't open $LogFileName $!\n";
while (<LOG>) 
{  
  my $curConnID=0; my $currUser=""; my $currDB="";
  my $curr=$_; chomp $curr; $curr =~ s/^\s+//;
  $curr =~ s/(^[0-9]+\s+[0-9][0-9]:[0-9][0-9]:[0-9][0-9])\s+//; 
  if ($1 =~ /(^[0-9]+\s+[0-9][0-9]:[0-9][0-9]:[0-9][0-9])/) 
    { if ($firstdate) { $finaldate=$1; } else { $firstdate=$1; } }
  if ( ! ( $curr =~ /(^[0-9]+\s+Query.*|^[0-9]+\s+Connect\s+.*\@localhost on|^[0-9]+\s+Init DB |^[0-9]+\s+Quit )/ ) ) {next;}
  if ( $curr =~ /^([0-9]+)(\s+Query.*)/ ) 
     {
     $curConnID=$1;
     if (exists($currhash{$curConnID})) { $QueriesNumber[$currhash{$curConnID}]++; }
     else 
        { if ( exists($unknownhash{$curConnID}) ) { $unknownhash{$curConnID}++; } 
          else { $unknownhash{$curConnID} = 1; } 
        }
     next;
     }

  if ( $curr =~ /([0-9]+\s+Connect\s+.*\@\S* on)/ ) 
     { 
       $curr=~ s/\s+Connect\s+/ /; $curr=~ s/ on / /;
       if ( $curr =~ /(^[0-9]+)\s+(\S+)\s*$/) { $curConnID=$1; $currUser=$2; $currDB=""; }
       if ( $curr =~ /(^[0-9]+)\s+(\S+)\s+(\S+)\s*$/) { $curConnID=$1; $currUser=$2; $currDB=$3; }
       if (exists($currhash{$curConnID})) { $QueriesNumber[$currhash{$curConnID}]++; }
       else { $ii=$#CID+1; $currhash{$curConnID}=$ii; $CID[$ii]=$curConnID;
              $MySQLUserName[$ii]=$currUser; $QueriesNumber[$ii]=0;
	      if ($currUser =~ /^(\S+)_.*\@.+$/) {$CpanelUserName[$ii]=$1;}
              if ($currUser =~ /^(\S+)\@\.+$/) {$CpanelUserName[$ii]=$1;}
              if ( ! ( $CpanelUserName[$ii] ) ) 
                { $CpanelUserName[$ii]=$currUser; $CpanelUserName[$ii] =~ s/\@.+$//;
                  $CpanelUserName[$ii] =~ s/_.+$//;
                } 
              if ( exists($unknownhash{$curConnID}) ) 
                { $QueriesNumber[$ii]=$unknownhash{$curConnID}; delete($unknownhash{$curConnID}); }
            }
     if ( $currDB ) { $DBName[$ii]=$currDB; }
     if ( ! ( $DBName[$ii] ) ) {if ($currUser =~ /^(\S+)\@.+$/) {$DBName[$ii]=$1; $currDB=$1;} }
     next;
     }

  if ( $curr =~ /^([0-9]+)\s+Init DB\s+(\S+)\s*$/ ) 
     {
      $curConnID=$1; $currDB=$2;
      if (exists($unknownhash{$curConnID})) 
        { 
          $QueriesNumber[$currhash{$curConnID}]++; delete($unknownhash{$curConnID});
          $DBName[$currhash{$curConnID}]=$currDB;
        }
      if (exists($currhash{$curConnID})) { $DBName[$currhash{$curConnID}]=$currDB;} 
      $curr=$currDB; $curr =~ s/\@.+$//; $curr =~ s/_.+$//;
      $CpanelUserName[$currhash{$curConnID}]=$curr; next;
     }

  if ( $curr =~ /^([0-9]+)( Quit )/ ) 
     {
      $curConnID=$1; delete $currhash{$curConnID}; next;
     }
}
my $iii=$.;
close (LOG);
#foreach $i (keys %unknownhash) { print "unknown=$i value $unknownhash{$i}\n"; }
for ($i=0; $i<=$#CID; $i++)
  {
    if ( ! ( exists($CIDhash{$CID[$i]}) ) ) { $CIDhash{$CID[$i]}=$QueriesNumber[$i]; } 
    else { $CIDhash{$CID[$i]}=$CIDhash{$CID[$i]}+$QueriesNumber[$i]; }
    if ( ! ( exists($DBhash{$DBName[$i]}) ) ) { $DBhash{$DBName[$i]}=$QueriesNumber[$i]; } 
    else { $DBhash{$DBName[$i]}=$DBhash{$DBName[$i]}+$QueriesNumber[$i]; }
    if ( ! ( exists($CpUNhash{$CpanelUserName[$i]}) ) ) { $CpUNhash{$CpanelUserName[$i]}=$QueriesNumber[$i]; } 
    else { $CpUNhash{$CpanelUserName[$i]}=$CpUNhash{$CpanelUserName[$i]}+$QueriesNumber[$i]; }
    if ( ! ( exists($MySQLUNhash{$MySQLUserName[$i]}) ) ) { $MySQLUNhash{$MySQLUserName[$i]}=$QueriesNumber[$i]; } 
    else { $MySQLUNhash{$MySQLUserName[$i]}=$MySQLUNhash{$MySQLUserName[$i]}+$QueriesNumber[$i]; }
  }
print "\nTop $top_number connection IDs:\n";
my @keys = sort { $CIDhash{$a} <=> $CIDhash{$b} } keys %CIDhash;
for ($i=$#keys; $i>$#keys-$top_number; $i--) { print "$keys[$i]      \t$CIDhash{$keys[$i]}\n"; }
print "\nTop $top_number MySQL users:\n";
@keys = sort { $MySQLUNhash{$a} <=> $MySQLUNhash{$b} } keys %MySQLUNhash;
for ($i=$#keys; $i>$#keys-$top_number; $i--) { print "$keys[$i]      \t$MySQLUNhash{$keys[$i]}\n"; }
print "\nTop $top_number MySQL Databases:\n";
@keys = sort { $DBhash{$a} <=> $DBhash{$b} } keys %DBhash;
for ($i=$#keys; $i>$#keys-$top_number; $i--) { print "$keys[$i]      \t$DBhash{$keys[$i]}\n"; }
print "\nTop $top_number cPanel users:\n";
@keys = sort { $CpUNhash{$a} <=> $CpUNhash{$b} } keys %CpUNhash;
for ($i=$#keys; $i>$#keys-$top_number; $i--) { print "$keys[$i]      \t$CpUNhash{$keys[$i]}\n"; }
$ii=0;
foreach $i (@QueriesNumber) { $ii=$ii+$i; }
print "\nStrings readed: $iii\n";
print "Total queries found: $ii\n";
print "First date: $firstdate\nLast date: $finaldate\n";
if ( $firstdate =~ /([0-9][0-9])([0-9][0-9])([0-9][0-9])\s+([0-9][0-9]):([0-9][0-9]):([0-9][0-9])/ ) 
{ $firstdate=timegm($6,$5,$4,$3,$2,$1);}
if ( $finaldate =~ /([0-9][0-9])([0-9][0-9])([0-9][0-9])\s+([0-9][0-9]):([0-9][0-9]):([0-9][0-9])/ ) 
{ $finaldate=timegm($6,$5,$4,$3,$2,$1);}
$i=$finaldate-$firstdate; print "Log length in seconds: $i\n";
$i=int(($ii/$i)*100); $i=$i/100; print "Queries per second avg: $i\n";
