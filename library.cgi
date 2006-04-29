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

# When I say 'UPC', what I actually mean is a EAN-13...
sub UPC_makecheckdigit($) {
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

sub UPC_checkcheckdigit($) {
	my ($upc) = @_;

	if (length($upc)!=13) {
		return undef;
	}

	my $check = chop($upc);
	return ($check == UPC_makecheckdigit($upc));
}

sub do_UPC($) {
	my ($q) = @_;
	my @r;
	my $upc = $q->param('UPC');

	push @r, 'upc:',$upc;
	push @r, '<pre>';

	if ($upc !~ /^\d+$/) {
		push @r, "Not a digit string\n";
		goto out;
	}

	if (!UPC_checkcheckdigit($upc)) {
		push @r, "Checksum not OK\n";
		goto out;
	}

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
			-script=>'function focus(){document.s.UPC.focus();}');

	push @result,
		# WTF TODO FIXME EVIL HACK
		# using this method causes some wierd undefined string warning
		#$q->start_form(-name=>'add'),
		'<form method="post" action="" enctype="multipart/form-data" name="s">',
		'UPC:',
		$q->textfield(-name=>'UPC', -value=>'', -override=>1,
			-size=>20, -maxlength=>20),
		$q->endform(),
		;

	if (defined $q->param('UPC')) {	
		push @result,
			do_UPC($q),
	}

	push @result,
		$q->end_html();


	print @result;
}

do_request();


