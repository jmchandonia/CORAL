#!/usr/bin/perl

use OBO::Parser::OBOParser;
use OBO::Core::Term;
use OBO::Core::Relationship;
use OBO::Core::RelationshipType;
use OBO::Core::Dbxref;
use OBO::Core::Synonym;
use Data::Dumper;
use File::Temp qw(tempfile tempdir);
use POSIX qw(strftime);
use strict;

my $ontology = shift;
my $prefix = shift;
my $txt = shift;
my $obo = shift;

# all terms found in text file
my @termsFound = ();

# object holding the units ontology
my $parser = OBO::Parser::OBOParser->new();
my $uo = $parser->work("/home/coral/prod/data_import/ontologies/uo.obo");
my $uo2 = $parser->work("/home/coral/prod/data_import/ontologies/context_measurement_ontology.obo");

# object holding the whole ontology
my $ont;

# current term in the ontology
my $term;

# is_a relationship
my $isa = "is_a";

if ($obo) {
    # load existing one, with old synonyms and properties filtered out
    my $dir = tempdir(CLEANUP => 1);
    my ($fh, $tmpfilename) = tempfile(DIR => $dir, SUFFIX => ".obo");
    system ("grep -v -e synonym: -e property_value: -e xref: $obo > $tmpfilename");
    $ont = $parser->work($tmpfilename);
}
else {
    # create from scratch
    $ont = OBO::Core::Ontology->new();
    $ont->saved_by("jmc");
    my $lcp = lc($prefix);
    $ont->id($lcp);

    $term = OBO::Core::Term->new();
    $term->id("$prefix:0000000");
    $term->name("term");
    my $def = OBO::Core::Def->new();
    $def->text("Root of all ontological terms.");
    $term->def($def);
    $term->namespace("$ontology.ontology");

    $ont->add_term($term);

    # define 'is_a' relationship
    $ont->add_relationship_type_as_string($isa,$isa);
}

# parse text file, keeping track of all parents of current term
my @parents = ();
my @parentScalars = ();
push @parents, "0000000";
push @parentScalars, "";
push @termsFound, "0000000";

my $lastIndent = 0;
my $id = 0;
my $nextID = 0;
# next ID should be 1+ highest ID currently in ontology
my @terms = @{$ont->get_terms()};
foreach $term (@terms) {
    $id = $term->id();
    $id =~ s/$prefix://;
    if ($id+1 > $nextID) {
	$nextID = $id+1;
    }
}
my $isNewTerm = 0;
open (INFILE,"<$txt");
while (<INFILE>) {
    chomp;
    # print ("$_\n");
    s/^( *)//;
    my $indent = length($1)/2;
    next if (length($_) < 1);
    if (/^ *#/) { # ignore full-line comments
	next;
    }
    s/ *#.*$//; # remove comments
    if (/alias: (.*)$/) {
	$term->synonym_as_string($1, "[]", "EXACT");
	next;
    }
    if (/is_a: (.*)$/) {
	my $parent = OBO::Core::Term->new();
	$parent->id("$1");
	$ont->create_rel($term,$isa,$parent);
	next;
    }
    s/^([^(]+): .*$/\1/;
    my $scalarType = "";
    if (/ +\((.*)\)/) {
	# capture scalar type
	$scalarType = $1;
	s/ +\((.*)\)//;
    }

    # check whether hidden: starts with "-"
    my $isHidden = 0;
    if (/^\-(.*)/) {
	$_ = $1;
	$isHidden = 1;
    }

    # check whether valid dimension only: starts with "**"
    my $isValidDimension = 0;
    my $isValidDimensionVar = 0;
    if (/^\*\*(.*)/) {
	$_ = $1;
	$isValidDimension = 1;
    }

    # check whether valid dimension: starts with "*"
    if (/^\*(.*)/) {
	$_ = $1;
	$isValidDimension = 1;
	$isValidDimensionVar = 1;
    }

    # check whether only dimension var, not dimension: starts with "*-"
    if (/^\-(.*)/) {
	$_ = $1;
	$isValidDimension = 0;
    }

    # check whether microtype (also valid property): starts with "+"
    my $isMicrotype = 0;
    my $isValidProperty = 0;
    my $isValidDataVar = 0;
    if (/^\+(.*)/) {
	$_ = $1;
	$isMicrotype = 1;
	$isValidProperty = 1;
	$isValidDataVar = 1;
    }

    # check whether reference to list of own children: ends with ":"
    my $isSelfRef = 0;
    if (/(.*):$/) {
	$_ = $1;
	$isSelfRef = 1;
    }

    $term = $ont->get_term_by_name($_);
    if (defined $term) {
	$id = $term->id();
	$id =~ s/$prefix://;
	# remember this term
	push @termsFound, $id;
    }
    else {
	$term = OBO::Core::Term->new();
	$id = sprintf("%07d",$nextID++);
	$term->id("$prefix:$id");
	$term->name($_);
	my $def = OBO::Core::Def->new();
	$def->text($_.".");
	$term->def($def);
	$term->namespace("$ontology.ontology");
	$isNewTerm = 1;
    }

    if ($scalarType =~ /Ref:/) {
	my @xrefs = split(/ or /,$scalarType);
	$scalarType = "";
	foreach my $xref (@xrefs) {
	    if ($xref =~ /Ref:/) {
		$term->xref_set_as_string("$xref");
		if ($xref =~ /ORef:/) {
		    $scalarType = "oterm_ref";
		}
		else {
		    $scalarType = "object_ref";
		}
	    }
	    else {
		$scalarType = $xref;
	    }
	}
    }
    for (my $i=0; $i<($lastIndent+1-$indent); $i++) {
	pop(@parents) if ($#parents > 0);
	pop(@parentScalars) if ($#parentScalars > 0);
    }
    my $parentID = pop(@parents);
    my $parentScalar = pop(@parentScalars);
    my $parent = $ont->get_term_by_id("$prefix:$parentID");
    if ($isNewTerm) {
	$ont->create_rel($term,$isa,$parent);
    }
    push @parents, $parentID;
    push @parents, $id;

    if ($isSelfRef) {
	$term->xref_set_as_string("ORef: ".$term->id());
	$scalarType = "oterm_ref";
    }

    # inherit scalar type from parent, if not set.
    # does not work for Refs/ORefs.
    push @parentScalars, $parentScalar;
    if (length($scalarType) == 0) {
	if ($parentScalar !~ /o\w+_ref/) {
	    $scalarType = $parentScalar;
	}
    }
    push @parentScalars, $scalarType;

    # if there's a scalar type, it's always a microtype
    if (length($scalarType) > 0) {
	$isMicrotype = 1;
	$isValidProperty = 1;
	$isValidDataVar = 1;
    }

    # dimension vars are automatically microtypes/properties
    if ($isValidDimensionVar) {
	$isMicrotype = 1;
	$isValidProperty = 1;
	$isValidDataVar = 1;
    }

    # dimensions are automatically microtypes, but not properties
    if ($isValidDimension) {
	$isMicrotype = 1;
    }

    # default microtype is string
    if (($isMicrotype) && (length($scalarType) == 0)) {
	$scalarType = "string";
    }

    if ($isValidDataVar) {
	my $src = OBO::Core::Instance->new();
	$src->id("is_valid_data_variable");
	my $targ = OBO::Core::Instance->new();
	$targ->id("\"true\" xsd:boolean");
	my $rel = OBO::Core::Relationship->new();
	$rel->id("is_valid_data_variable");
	$rel->type("is_valid_data_variable");
	$rel->link($src,$targ);
	$term->property_value($rel);
    }
    if ($isValidDimensionVar) {
	my $src = OBO::Core::Instance->new();
	$src->id("is_valid_dimension_variable");
	my $targ = OBO::Core::Instance->new();
	$targ->id("\"true\" xsd:boolean");
	my $rel = OBO::Core::Relationship->new();
	$rel->id("is_valid_dimension_variable");
	$rel->type("is_valid_dimension_variable");
	$rel->link($src,$targ);
	$term->property_value($rel);
    }
    if ($isValidDimension) {
	my $src = OBO::Core::Instance->new();
	$src->id("is_valid_dimension");
	my $targ = OBO::Core::Instance->new();
	$targ->id("\"true\" xsd:boolean");
	my $rel = OBO::Core::Relationship->new();
	$rel->id("is_valid_dimension");
	$rel->type("is_valid_dimension");
	$rel->link($src,$targ);
	$term->property_value($rel);
    }
    if ($isMicrotype) {
	my $src = OBO::Core::Instance->new();
	$src->id("is_microtype");
	my $targ = OBO::Core::Instance->new();
	$targ->id("\"true\" xsd:boolean");
	my $rel = OBO::Core::Relationship->new();
	$rel->id("is_microtype");
	$rel->type("is_microtype");
	$rel->link($src,$targ);
	$term->property_value($rel);
    }
    if ($isValidProperty) {
	my $src = OBO::Core::Instance->new();
	$src->id("is_valid_property");
	my $targ = OBO::Core::Instance->new();
	$targ->id("\"true\" xsd:boolean");
	my $rel = OBO::Core::Relationship->new();
	$rel->id("is_valid_property");
	$rel->type("is_valid_property");
	$rel->link($src,$targ);
	$term->property_value($rel);
    }
    if ($isHidden) {
	my $src = OBO::Core::Instance->new();
	$src->id("is_hidden");
	my $targ = OBO::Core::Instance->new();
	$targ->id("\"true\" xsd:boolean");
	my $rel = OBO::Core::Relationship->new();
	$rel->id("is_hidden");
	$rel->type("is_hidden");
	$rel->link($src,$targ);
	$term->property_value($rel);
    }
    if (length($scalarType) > 1) {
	if ($scalarType =~ /(.*?), (.*)/) {
	    $scalarType = $1;
	    my $units = $2;
	    my $unitIDs = "";
	    my $parentUnitIDs = "";
	    my $includeParent = 0;
	    foreach my $unit (split(/, /,$units)) {
		if ($unit =~ /^\+/) {
		    $unit =~ s/^\+//;
		    $includeParent = 1;
		}
		my $unitsTerm = $uo->get_term_by_name_or_synonym($unit);
		my $hasChildren = 0;
		if (defined $unitsTerm) {
		    $hasChildren = (scalar @{$uo->get_relationships_by_target_term($unitsTerm,$isa)} > 0);
		}
		else {
		    $unitsTerm = $uo2->get_term_by_name_or_synonym($unit);
		    if (defined $unitsTerm) {
			$hasChildren = (scalar @{$uo2->get_relationships_by_target_term($unitsTerm,$isa)} > 0);
		    }
		    else {
			die("No units term found for \"$unit\"");
		    }
		}
		if ($hasChildren) {
		    # count only as parent, unless includeParent set
		    if (length($parentUnitIDs) > 0) {
			$parentUnitIDs .= " ";
		    }
		    $parentUnitIDs .= $unitsTerm->id;
		}
		if ((!$hasChildren) || ($includeParent)) {
		    if (length($unitIDs) > 0) {
			$unitIDs .= " ";
		    }
		    $unitIDs .= $unitsTerm->id;
		}
	    }
	    if (length($parentUnitIDs) > 0) {
		my $pv = "valid_units_parent";
		my $src = OBO::Core::Instance->new();
		$src->id($pv);
		my $targ = OBO::Core::Instance->new();
		$targ->id("\"$parentUnitIDs\" xsd:string");
		my $rel = OBO::Core::Relationship->new();
		$rel->id($pv);
		$rel->type($pv);
		$rel->link($src,$targ);
		$term->property_value($rel);
	    }
	    if (length($unitIDs) > 0) {
		my $pv = "valid_units";
		my $src = OBO::Core::Instance->new();
		$src->id($pv);
		my $targ = OBO::Core::Instance->new();
		$targ->id("\"$unitIDs\" xsd:string");
		my $rel = OBO::Core::Relationship->new();
		$rel->id($pv);
		$rel->type($pv);
		$rel->link($src,$targ);
		$term->property_value($rel);
	    }
	}
	$scalarType = lc($scalarType);
	my $src = OBO::Core::Instance->new();
	$src->id("data_type");
	my $targ = OBO::Core::Instance->new();
	$targ->id("\"$scalarType\" xsd:string");
	my $rel = OBO::Core::Relationship->new();
	$rel->id("data_type");
	$rel->type("data_type");
	$rel->link($src,$targ);
	$term->property_value($rel);
    }

    $lastIndent = $indent;
}

# delete any terms no longer in text file
foreach $term (@terms) {
    $id = $term->id();
    $id =~ s/$prefix://;
    if (! grep {$_ eq $id} @termsFound) {
	$ont->delete_term($term);
    }
}

# version it with today's date
my $today = strftime('%Y-%m-%d', localtime);
$ont->data_version($today);

$ont->export('obo', \*STDOUT);
