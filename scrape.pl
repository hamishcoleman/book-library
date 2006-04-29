#!/usr/bin/perl -w
use strict;
#
# Simple test of the WWW::Scraper::ISBN library
#

use WWW::Scraper::ISBN;
use Data::Dumper;

my $scraper = WWW::Scraper::ISBN->new();
$scraper->drivers("AmazonUK","AmazonUS");

my $isbn = $ARGV[0] || "123456789X";

my $record = $scraper->search($isbn);
if($record->found) {
	print "Book ".$record->isbn." found by driver ".$record->found_in."\n";
	my $book = $record->book;
	# do stuff with book hash
	print "Title:  ",$book->{'title'},"\n";
	print "Author: ",$book->{'author'},"\n";
	# etc
} else {
       print $record->error;
}

print "\n";
print Dumper($record);

