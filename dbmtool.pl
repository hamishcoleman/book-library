#!/usr/bin/perl -w
use warnings;
use strict;
#
# Keep a local database file of ISBN information
#

my %db;		# urk. global database

use DB_File;

my $debug;

tie %db, 'DB_File', 'database.dbm', O_CREAT|O_RDONLY or die "could not open dbm";

my $cmd = $ARGV[0];
my $key = $ARGV[1];

if ($cmd) {
	if ($cmd eq 'get') {
		if ( ! $db{$key} ) {
			print "not stored";
		} else {
			print $db{$key};
		}
	} elsif ($cmd eq 'set') {
		$db{$key} = $ARGV[2];
		print "Setting $key to $ARGV[2]\n";
	} elsif ($cmd eq 'del') {
		delete $db{$key};
	} elsif ($cmd eq 'list') {
		my @l = keys %db;
		print join "\n", sort @l;
	}
	exit;
}

