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
use XML::LibXML;

use Data::Dumper;
$Data::Dumper::Indent = 1;
$Data::Dumper::Sortkeys = 1;


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

sub http_setup() {
	use LWP::UserAgent;
	use HTTP::Cookies;
	my $ua = LWP::UserAgent->new;
	$ua->agent("Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.3) Gecko/20070310");
	$ua->cookie_jar(HTTP::Cookies->new());

	# LWP talks about RFC 2616 when it says that POST's cannot redirect
	# I have looked up the standard and it does not appear to say that
	#
	# FIXME - find out why LWP wants this in the face of the above comment
	push @{ $ua->requests_redirectable }, 'POST';

	return $ua;
}

sub isbn_get($$$) {
	my ($ua,$key,$isbn) = @_;

	my $url = "http://isbndb.com/api/books.xml?access_key=$key&results=details,texts,prices,authors,keystats&index1=isbn&value1=$isbn";

	my $req = HTTP::Request->new(GET => $url);
	my $res = $ua->request($req);
	#dump_res('get',$res);

	return $res;
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

# FIXME - globals
my $parser = XML::LibXML->new();
sub isbn_xml($) {
	my ($db) = @_;

	my $doc = $parser->parse_string($db->{xml});
	if (!$doc) { $db->{error}='!doc'; return $db; }
	my $root = $doc->getDocumentElement();

	my $isbndb = $root;
	#for my $i ($root->getElementsByTagName('ISBNdb')) {$isbndb=$i;}
	if (!$isbndb) { $db->{error}='!ISBNdb'; return $db; }
	
	my $keystats = ($isbndb->getElementsByTagName('KeyStats'))[0];
	if (!$isbndb) { $db->{error}='!KeyStats'; return $db; }
	
	$db->{KeyStats}->{granted} = $keystats->getAttribute('granted');

	my $booklist = ($isbndb->getElementsByTagName('BookList'))[0];
	if (!$booklist) { $db->{error}='!BookList'; return $db; }

	$db->{BookList}->{shown_results} = $booklist->getAttribute('shown_results');

	for my $book ($booklist->getElementsByTagName('BookData')) {
		my $id = $book->getAttribute('book_id');
		$db->{BookData}->{$id}={};
		my $entry = $db->{BookData}->{$id};

		$entry->{ISBN} = $book->getAttribute('isbn');

		$entry->{Title} = ($book->getElementsByTagName('Title'))[0]->textContent();
		#$entry->{AuthorsText} = ($book->getElementsByTagName('AuthorsText'))[0]->textContent();
		$entry->{Summary} = ($book->getElementsByTagName('Summary'))[0]->textContent();

		my $prices = ($isbndb->getElementsByTagName('Prices'))[0];
		for my $price ($prices->getElementsByTagName('Price')) {
			my $id = $price->getAttribute('store_id');

			$entry->{Prices}->{$id}->{currency} = $price->getAttribute('currency_code');
			$entry->{Prices}->{$id}->{price} = $price->getAttribute('price');
		}

		my $authors = ($isbndb->getElementsByTagName('Authors'))[0];
		for my $person ($authors->getElementsByTagName('Person')) {
			my $id = $person->getAttribute('person_id');

			$entry->{Authors}->{$id} = $person->textContent();
		}
	}

	return $db;
}

sub emit_tr($) {
	my ($db) = @_;
	my @r;
		
	for my $book_id (keys %{$db->{BookData}}) {
		my $book = $db->{BookData}->{$book_id};
		push @r,'<tr>';
		push @r,'<td>',$book->{ISBN},'</td>';
		push @r,'<td>',$book->{Title},'</td>';
		push @r,'<td>';
		for my $person_id (keys %{$book->{Authors}}) {
			push @r,$book->{Authors}->{$person_id},'<br/>';
		}
		push @r,'</td>';
		push @r,'<td>',$book->{Summary},'</td>';
		push @r,'</tr>';
	}
	
	return @r;
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

sub do_validate($$) {
	my ($db,$search) = @_;
	my @r;

	# Remove unwanted characters
	$search =~ s/[ -]+//g;
	$db->{search} = $search;

	# Validate contents as digits and x only
	if ($search !~ /^[\dxX]+$/) {
		$db->{type} = "NONDIGIT";
		push @r, "Validate: search is not a digit or x\n";
		return @r;
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
	return @r;
}

sub do_normalise($) {
	my ($db) = @_;
	my @r;
	
	if ($db->{type} eq 'EAN13') {
		my $prefix = substr($db->{search},0,3);

		if ($prefix eq '978') {
			# convert to 'old' ISBN format
			my $isbn = substr($db->{search},3);
			chop($isbn);
			my $isbncheck = ISBN_makecheckdigit($isbn);
			if (!defined $isbncheck) {
				push @r, "length error in isbn check digit generation\n";
				goto out;
			}
			$db->{search} = $isbn . $isbncheck;
			$db->{type} = "ISBN";
			$db->{origtype} = "EAN13 Bookland";
		}

		if ($prefix eq '979') {
			$db->{type} = "ISBN";
			$db->{origtype} = "EAN13";
		}
	}
	return @r;
}

sub do_search($) {
	my ($db) = @_;
	my @r;

	push @r, "Type: $db->{type}\n\n";

	if ($db->{type} eq 'ISBN') {
		my $ua = http_setup();
		$db->{xml} = isbn_get($ua,'CHANGEME',$db->{search})->content;
	}

	return @r;
}

sub do_request() {
	my $q = new CGI;
	my $db = {};
	my @result;
	my @result_head;

	print $q->header();
	push @result_head,
		$q->start_html(
			-title=>'simple library interface',
			-onLoad=>'focus()',
			-script=>'function focus(){document.s.search.focus();}');

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
		my $search = $q->param('search');
		push @result, "<pre>\n";
		push @result, "Search: $search\n";

		push @result, do_validate($db,$search);
		push @result, do_normalise($db);
		push @result, do_search($db);

		push @result, Dumper(isbn_xml($db));

		push @result_head,"<table border='2' cellpadding='4' cellspacing='0' style='margin: 1em 1em 1em 0; background: #f9f9f9; border: 1px #aaa solid; border-collapse: collapse; font-size: 95%;'>";
		push @result_head,"<tr><th>ISBN<th>Title<th>Author<th>Summary</tr>";

		push @result_head, emit_tr($db);
		push @result_head,"</table>";

		#push @result, $db->{xml};

		push @result, '</pre>';
	}

	push @result,
		$q->end_html();


	print @result_head, @result;

	#print Dumper(\@result);
}

do_request();

