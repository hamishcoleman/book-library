#!/usr/bin/perl -w
package ISBNValidate;
use Exporter;
@ISA = qw(Exporter);
@EXPORT = qw(is_ISBN);
#
use warnings;
use strict;
#
# ISBN validation
#

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
	return ($check eq ISBN_makecheckdigit($s));
}

# Checks if a given string looks like a valid ISBN.
# if it is, return a normalised version of the string
sub is_ISBN($) {
	my ($s) = @_;
	my $type;

	# Remove unwanted characters
	$s =~ s/[ -]+//g;

	# Ensure consistant case
	$s = uc $s;

	# Validate contents as digits and x only
	if ($s !~ /^[\d]+[\dX]$/) {
		return undef;
	}
	
	if (EAN13_checkcheckdigit($s)) {
		$type = "EAN13";

		if (substr($s,0,3) eq '978') {
			# convert bookland to 'old' ISBN format
			my $isbn = substr($s,3);
			chop($isbn);
			my $isbncheck = ISBN_makecheckdigit($isbn);
			if (!defined $isbncheck) {
				die "error in isbn check digit generation\n";
			}
			$s = $isbn . $isbncheck;
			$type = "ISBN";
		}
	} elsif (ISBN_checkcheckdigit($s)) {
		$type = "ISBN";
	} elsif (length($s)==9 &&
		ISBN_checkcheckdigit('0'.$s)) {
		$type = "ISBN9";
		$s = '0'.$s;
	} else {
		return undef;
	}

	return $s;
}

#while( $ARGV[0] ) {
#	my $isbn = is_ISBN($ARGV[0]);
#	print ($ARGV[0],"\t",$isbn||'ERROR',"\n");
#	pop @ARGV;
#}

1;
