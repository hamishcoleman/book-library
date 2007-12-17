#!/usr/bin/perl -w
use strict;
#
# simple library system interface
#

#glob $library::db = "db/library.sql";

##########################################################################
#
# Libs we need.
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use Data::Dumper;


sub EAN13_makecheckdigit($) {
	my ($upc) = @_;

	if (length($upc)!=12) {
		# EAN-13 without check digit is 12 chars long
		return undef;
	}

	my $csum=0;
	while ($upc) {
		$csum+= (chop $upc)*3;
		$csum+=  chop $upc;
	}
	my $modulus = 10 - ($csum%10);
	if ($modulus == 10) {
		return 0;
	} else {
		return $modulus;
	}
}

sub EAN13_checkcheckdigit($) {
	my ($upc) = @_;

	if (length($upc)!=13) {
		return undef;
	}

	my $check = chop($upc);
	return ($check == EAN13_makecheckdigit($upc));
}

sub ISBN_makecheckdigit($) {
	my ($isbn) = @_;

	if (length($isbn)!=9) {
		# ISBN-10 without check digit
		return undef;
	}

	my $csum;
	$csum+= 1* substr($isbn,0,1);
	$csum+= 2* substr($isbn,1,1);
	$csum+= 3* substr($isbn,2,1);
	$csum+= 4* substr($isbn,3,1);
	$csum+= 5* substr($isbn,4,1);
	$csum+= 6* substr($isbn,5,1);
	$csum+= 7* substr($isbn,6,1);
	$csum+= 8* substr($isbn,7,1);
	$csum+= 9* substr($isbn,8,1);
	$csum %= 11;

	if ($csum == 10) {
		return 'X';
	} else {
		return $csum;
	}
}

sub ISBN_checkcheckdigit($) {
	my ($s) = @_;

	if (length($s)!=10) {
		return undef;
	}

	my $check = chop($s);
	return ($check == ISBN_makecheckdigit($s));
}

sub do_ISBN($) {
	my ($isbn) = @_;
	my @r;

	# the scraper is a) broken, b) constantly rebreaks, c) annoying to install, d) superceeded
	return;

#	my $scraper = WWW::Scraper::ISBN->new();
#	$scraper->drivers("AmazonUS");
#
#	my $record = $scraper->search($isbn);
#	if($record->found) {
#		push @r, "ISBN: ",$record->isbn,"\n",
#			"driver: ",$record->found_in,"\n";
#
#		my $book = $record->book;
#		# do stuff with book hash
#		push @r, "Title:  ",$book->{'title'},"\n";
#		push @r, "Author: ",$book->{'author'},"\n";
#
#	} else {
#		push @r, "Error: ",$record->error;
#	}
#
#	#print Dumper($record);
#	return @r;
}

sub do_UPC($$) {
	my ($q,$search) = @_;
	my @r;

	push @r, "<pre>\n";
	push @r, "search: $search\n";

	if ($search !~ /^\d+$/) {
		push @r, "Not a digit string\n";
		goto out;
	}

	if (!EAN13_checkcheckdigit($search)) {
		push @r, "Checksum not OK\n";
		goto out;
	}
	push @r, "EAN13\n";

	# TODO - have a	list of other countries?
	# FIXME - determine what function bookland 979 has
	if ($search =~ /^(978)/) {
		push @r, "Bookland!\n";

		my $isbn = substr($search,3);
		chop($isbn);
		my $isbncheck = ISBN_makecheckdigit($isbn);
		if (!defined $isbncheck) {
			push @r, "length error in isbn check digit generation\n";
			goto out;
		}
		$isbn .= $isbncheck;
		push @r, "ISBN: $isbn ";
		push @r, $q->a({href=>"http://www.amazon.com/exec/obidos/ISBN=$isbn/"},"Amazon.com"),"\n";
		push @r, do_ISBN($isbn);
	}

out:
	push @r, '</pre>';

	return @r;
}

sub do_search($$) {
	my ($q,$search) = @_;
	my $db;
	my @r;


	push @r, "<pre>\n";
	push @r, "Search: $search\n";

	# Remove unwanted characters
	$search =~ s/[ -]+//g;
	$db->{search} = $search;

	# Validate contents as digits and x only
	if ($search !~ /^[\dxX]+$/) {
		$db->{type} = "NONDIGIT";
		push @r, "Validate: search is not a digit or x\n";
		goto out;
	}
	
	if (EAN13_checkcheckdigit($search)) {
		$db->{type} = "EAN13";
		push @r, "Validate: EAN13: Valid\n";
	} else {
		push @r, "Validate: EAN13: Invalid\n";
	}

	if (ISBN_checkcheckdigit($search)) {
		$db->{type} = "ISBN";
		push @r, "Validate: ISBN: Valid\n";
	} else {
		push @r, "Validate: ISBN: Invalid\n";
	}

	if (length($search)==9 &&
		ISBN_checkcheckdigit('0'.$search)) {
		$db->{search} = '0'.$search;
		$db->{type} = "ISBN";
		$db->{origtype} = "ISBN 9 digit";
		push @r, "Validate: ISBN 9 digit: Valid\n";
	} else {
		push @r, "Validate: ISBN 9 digit: Invalid\n";
	}

	if ($db->{type} eq 'EAN13') {
		my $prefix = substr($db->{search},0,3);
		if ($prefix eq '978' || $prefix eq '979') {
			$db->{type} = "ISBN";
			$db->{origtype} = "EAN13";
		}
	}

	push @r, "Type: $db->{type}\n";

out:
	push @r, '</pre>';
	return @r;
}

sub do_request() {
	my $q = new CGI;
	my @result;

	print $q->header();
	push @result,
		$q->start_html(
			-title=>'simple library interface',
			-onLoad=>'focus()',
			-script=>'function focus(){document.s.code.focus();}');

	push @result,
		# WTF TODO FIXME EVIL HACK
		# using this method causes some wierd undefined string warning
		#$q->start_form(-name=>'s'),
		'<form method="post" action="" enctype="multipart/form-data" name="s">',
		'Search:',
		$q->textfield(-name=>'search', -value=>'', -override=>1,
			-size=>20),
		$q->endform(),
		;

	if (defined $q->param('search')) {
		push @result,
			do_search($q,$q->param('search')),
	}

	push @result,
		$q->end_html();


	print @result;

	#print Dumper(\@result);
}

do_request();

