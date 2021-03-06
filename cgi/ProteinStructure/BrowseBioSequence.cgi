#!/usr/local/bin/perl

###############################################################################
# Program     : BrowseBioSequence.cgi
# Author      : Eric Deutsch <edeutsch@systemsbiology.org>
# $Id$
#
# Description : This CGI program that allows users to
#               browse through BioSequences.
#
# SBEAMS is Copyright (C) 2000-2005 Institute for Systems Biology
# This program is governed by the terms of the GNU General Public License (GPL)
# version 2 as published by the Free Software Foundation.  It is provided
# WITHOUT ANY WARRANTY.  See the full description of GPL terms in the
# LICENSE file distributed with this software.
#
###############################################################################


###############################################################################
# Set up all needed modules and objects
###############################################################################
use strict;
use Getopt::Long;
use FindBin;

use lib "$FindBin::Bin/../../lib/perl";
use vars qw ($sbeams $sbeamsMOD $q $current_contact_id $current_username
             $PROG_NAME $USAGE %OPTIONS $QUIET $VERBOSE $DEBUG $DATABASE
             $TABLE_NAME $PROGRAM_FILE_NAME $CATEGORY $DB_TABLE_NAME
             @MENU_OPTIONS);

use SBEAMS::Connection qw($q);
use SBEAMS::Connection::Settings;
use SBEAMS::Connection::Tables;

use SBEAMS::ProteinStructure;
use SBEAMS::ProteinStructure::Settings;
use SBEAMS::ProteinStructure::Tables;

$sbeams = new SBEAMS::Connection;
$sbeamsMOD = new SBEAMS::ProteinStructure;
$sbeamsMOD->setSBEAMS($sbeams);
$sbeams->setSBEAMS_SUBDIR($SBEAMS_SUBDIR);


#use CGI;
use CGI::Carp qw(fatalsToBrowser croak);
#$q = new CGI;


###############################################################################
# Set program name and usage banner for command like use
###############################################################################
$PROG_NAME = $FindBin::Script;
$USAGE = <<EOU;
Usage: $PROG_NAME [OPTIONS] key=value key=value ...
Options:
  --verbose n         Set verbosity level.  default is 0
  --quiet             Set flag to print nothing at all except errors
  --debug n           Set debug flag

 e.g.:  $PROG_NAME [OPTIONS] [keyword=value],...

EOU

#### Process options
unless (GetOptions(\%OPTIONS,"verbose:s","quiet","debug:s")) {
  print "$USAGE";
  exit;
}

$VERBOSE = $OPTIONS{"verbose"} || 0;
$QUIET = $OPTIONS{"quiet"} || 0;
$DEBUG = $OPTIONS{"debug"} || 0;
if ($DEBUG) {
  print "Options settings:\n";
  print "  VERBOSE = $VERBOSE\n";
  print "  QUIET = $QUIET\n";
  print "  DEBUG = $DEBUG\n";
}


###############################################################################
# Set Global Variables and execute main()
###############################################################################
main();
exit(0);


###############################################################################
# Main Program:
#
# Call $sbeams->Authenticate() and exit if it fails or continue if it works.
###############################################################################
sub main {

  #### Do the SBEAMS authentication and exit if a username is not returned
  exit unless ($current_username = $sbeams->Authenticate(
    permitted_work_groups_ref=>['ProteinStructure_user',
      'ProteinStructure_admin','ProteinStructure_readonly','Admin'],
    #connect_read_only=>1,
    #allow_anonymous_access=>1,
  ));


  #### Read in the default input parameters
  my %parameters;
  my $n_params_found = $sbeams->parse_input_parameters(
    q=>$q,parameters_ref=>\%parameters);
  #$sbeams->printDebuggingInfo($q);


  #### Process generic "state" parameters before we start
  $sbeams->processStandardParameters(parameters_ref=>\%parameters);


  #### Decide what action to take based on information so far
  if ($parameters{action} eq "UPDATE") {
  } else {
    $sbeamsMOD->display_page_header(
      navigation_bar=>$parameters{navigation_bar});
    handle_request(ref_parameters=>\%parameters);
    $sbeamsMOD->display_page_footer();
  }


} # end main



###############################################################################
# Handle Request
###############################################################################
sub handle_request {
  my %args = @_;


  #### Process the arguments list
  my $ref_parameters = $args{'ref_parameters'}
    || die "ref_parameters not passed";
  my %parameters = %{$ref_parameters};


  #### Define some generic varibles
  my ($i,$element,$key,$value,$line,$result,$sql);


  #### Define some variables for a query and resultset
  my %resultset = ();
  my $resultset_ref = \%resultset;
  my (%url_cols,%hidden_cols,%max_widths,$show_sql);


  #### Read in the standard form values
  my $apply_action  = $parameters{'action'} || $parameters{'apply_action'};
  my $TABLE_NAME = $parameters{'QUERY_NAME'};

  my $search_hit_id  = $q->param('search_hit_id');
  my $label_peptide  = $q->param('label_peptide') || '';
  my $label_start  = $q->param('label_start') || '';
  my $label_end  = $q->param('label_end') || '';


  #### Set some specific settings for this program
  my $CATEGORY="BioSequence Search";
  $TABLE_NAME="PS_BrowseBioSequence" unless ($TABLE_NAME);
  ($PROGRAM_FILE_NAME) =
    $sbeamsMOD->returnTableInfo($TABLE_NAME,"PROGRAM_FILE_NAME");
  my $base_url = "$CGI_BASE_DIR/$SBEAMS_SUBDIR/$PROGRAM_FILE_NAME";


  #### Get the columns and input types for this table/query
  my @columns = $sbeamsMOD->returnTableInfo($TABLE_NAME,"ordered_columns");
  my %input_types = 
    $sbeamsMOD->returnTableInfo($TABLE_NAME,"input_types");


  #### Read the input parameters for each column
  my $n_params_found = $sbeams->parse_input_parameters(
    q=>$q,parameters_ref=>\%parameters,
    columns_ref=>\@columns,input_types_ref=>\%input_types);


  #### If the apply action was to recall a previous resultset, do it
  my %rs_params = $sbeams->parseResultSetParams(q=>$q);
  if ($apply_action eq "VIEWRESULTSET") {
    $sbeams->readResultSet(resultset_file=>$rs_params{set_name},
        resultset_ref=>$resultset_ref,query_parameters_ref=>\%parameters);
    $n_params_found = 99;
  }


  #### Set some reasonable defaults if no parameters supplied
  unless ($n_params_found) {
  }


  #### Apply any parameter adjustment logic


  #### Display the user-interaction input form
  $sbeams->display_input_form(
    TABLE_NAME=>$TABLE_NAME,CATEGORY=>$CATEGORY,apply_action=>$apply_action,
    PROGRAM_FILE_NAME=>$PROGRAM_FILE_NAME,
    parameters_ref=>\%parameters,
    input_types_ref=>\%input_types,
    mask_user_context => 0,
    allow_NOT_flags => 1,
  );


  #### Display the form action buttons
  $sbeams->display_form_buttons(TABLE_NAME=>$TABLE_NAME);


  #### Finish the upper part of the page and go begin the full-width
  #### data portion of the page
  $sbeams->display_page_footer(close_tables=>'YES',
    separator_bar=>'YES',display_footer=>'NO')
    unless ( $parameters{display_options} =~ /SequenceFormat/ &&
      $apply_action =~ /HIDE/ );



  #########################################################################
  #### Process all the constraints

  #### Build BIOSEQUENCE_SET constraint
  my $form_test = $sbeams->parseConstraint2SQL(
    constraint_column=>"BS.biosequence_set_id",
    constraint_type=>"int_list",
    constraint_name=>"BioSequence Set",
    constraint_value=>$parameters{biosequence_set_id} );
  return if ($form_test eq '-1');

  #### Verify that the selected biosequence_sets are permitted
  if ($parameters{biosequence_set_id}) {
    my $sql = qq~
      SELECT biosequence_set_id,project_id
	FROM $TBPS_BIOSEQUENCE_SET
       WHERE biosequence_set_id IN ( $parameters{biosequence_set_id} )
	 AND record_status != 'D'
    ~;
    my %project_ids = $sbeams->selectTwoColumnHash($sql);
    my @accessible_project_ids = $sbeams->getAccessibleProjects();
    my %accessible_project_ids;
    foreach my $id ( @accessible_project_ids ) {
      $accessible_project_ids{$id} = 1;
    }

    my @input_ids = split(',',$parameters{biosequence_set_id});
    my @verified_ids;
    foreach my $id ( @input_ids ) {

      #### If the requested biosequence_set_id doesn't exist
      if (! defined($project_ids{$id})) {
	$sbeams->reportException(
          state => 'ERROR',
          type => 'BAD CONSTRAINT',
          message => "Non-existent biosequence_set_id = $id specified",
        );

      #### If the project for this biosequence_set is not accessible
      } elsif (! defined($accessible_project_ids{$project_ids{$id}})) {
	$sbeams->reportException(
          state => 'ERROR',
          type => 'PERMISSION DENIED',
          message => "Your current privilege settings do not allow you to access biosequence_set_id = $id.  See project owner to gain permission.",
        );

      #### Else, let it through
      } else {
	push(@verified_ids,$id);
      }

    }

    #### Set the input constraint to only allow that which is valid
    $parameters{biosequence_set_id} = join(',',@verified_ids);

  }

  #### If no valid biosequence_set_id was selected, stop here
  unless ($parameters{biosequence_set_id}) {
    $sbeams->reportException(
      state => 'ERROR',
      type => 'INSUFFICIENT CONSTRAINTS',
      message => "You must select at least one valid Biosequence Set",
    );
    return;
  }

  #### Build BIOSEQUENCE_SET constraint
  my $biosequence_set_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"BS.biosequence_set_id",
    constraint_type=>"int_list",
    constraint_name=>"BioSequence Set",
    constraint_value=>$parameters{biosequence_set_id} );
  return if ($biosequence_set_clause eq '-1');


  #### Build BIOSEQUENCE constraint
  my $biosequence_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"BS.biosequence_id",
    constraint_type=>"int_list",
    constraint_name=>"BioSequence",
    constraint_value=>$parameters{biosequence_id_constraint} );
  return if ($biosequence_clause eq '-1');

  #### Build BIOSEQUENCE_NAME constraint
  my $biosequence_name_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"BS.biosequence_name",
    constraint_type=>"plain_text",
    constraint_name=>"BioSequence Name",
    constraint_value=>$parameters{biosequence_name_constraint},
    constraint_NOT_flag=>$parameters{"NOT_biosequence_name_constraint"},
  );
  return if ($biosequence_name_clause eq '-1');


  #### Build BIOSEQUENCE_ACCESSION constraint
  my $biosequence_accession_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"BS.biosequence_accession",
    constraint_type=>"plain_text",
    constraint_name=>"BioSequence Accession",
    constraint_value=>$parameters{biosequence_accession_constraint},
    constraint_NOT_flag=>$parameters{"NOT_biosequence_accession_constraint"},
  );
  return if ($biosequence_accession_clause eq '-1');


  #### Build BIOSEQUENCE_GENE_NAME constraint
  my $biosequence_gene_name_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"BS.biosequence_gene_name",
    constraint_type=>"plain_text",
    constraint_name=>"BioSequence Gene Name",
    constraint_value=>$parameters{biosequence_gene_name_constraint},
    constraint_NOT_flag=>$parameters{"NOT_biosequence_gene_name_constraint"},
  );
  return if ($biosequence_gene_name_clause eq '-1');


  #### Build BIOSEQUENCE_SEQ constraint
  my $biosequence_seq_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"BS.biosequence_seq",
    constraint_type=>"plain_text",
    constraint_name=>"BioSequence Sequence",
    constraint_value=>$parameters{biosequence_seq_constraint},
    constraint_NOT_flag=>$parameters{"NOT_biosequence_seq_constraint"},
  );
  return if ($biosequence_seq_clause eq '-1');
  $biosequence_seq_clause =~ s/\*/\%/g;


  #### Build BIOSEQUENCE_DESC constraint
  my $biosequence_desc_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"BS.biosequence_desc",
    constraint_type=>"plain_text",
    constraint_name=>"BioSequence Description",
    constraint_value=>$parameters{biosequence_desc_constraint},
    constraint_NOT_flag=>$parameters{"NOT_biosequence_desc_constraint"},
  );
  return if ($biosequence_desc_clause eq '-1');


  #### Build MOLECULAR FUNCTION constraint
  my $molecular_function_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"MFA.annotation",
    constraint_type=>"plain_text",
    constraint_name=>"Molecular Function",
    constraint_value=>$parameters{molecular_function_constraint},
    constraint_NOT_flag=>$parameters{"NOT_molecular_function_constraint"},
  );
  return if ($molecular_function_clause eq '-1');


  #### Build BIOLOGICAL PROCESS constraint
  my $biological_process_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"BPA.annotation",
    constraint_type=>"plain_text",
    constraint_name=>"Biological Process",
    constraint_value=>$parameters{biological_process_constraint},
    constraint_NOT_flag=>$parameters{"NOT_biological_process_constraint"},
  );
  return if ($biological_process_clause eq '-1');


  #### Build CELLULAR COMPONENT constraint
  my $cellular_component_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"CCA.annotation",
    constraint_type=>"plain_text",
    constraint_name=>"Cellular Component",
    constraint_value=>$parameters{cellular_component_constraint},
    constraint_NOT_flag=>$parameters{"NOT_cellular_component_constraint"},
  );
  return if ($cellular_component_clause eq '-1');


  #### Build INTERPRO PROTEIN DOMAIN constraint
  my $protein_domain_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"IPDA.annotation",
    constraint_type=>"plain_text",
    constraint_name=>"InterPro Protein Domain",
    constraint_value=>$parameters{protein_domain_constraint},
    constraint_NOT_flag=>$parameters{"NOT_protein_domain_constraint"},
  );
  return if ($protein_domain_clause eq '-1');


#  #### Build FAVORED CODON FREQUENCY constraint
#  my $fav_codon_frequency_clause = $sbeams->parseConstraint2SQL(
#    constraint_column=>"BS.fav_codon_frequency",
#    constraint_type=>"flexible_float",
#    constraint_name=>"Favored Codon Frequency",
#    constraint_value=>$parameters{fav_codon_frequency_constraint} );
#  return if ($fav_codon_frequency_clause eq '-1');


  #### Build PROTEIN LENGTH constraint
  my $protein_length_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"DATALENGTH(BS.biosequence_seq)",
    constraint_type=>"flexible_int",
    constraint_name=>"Protein Length",
    constraint_value=>$parameters{protein_length_constraint} );
  return if ($protein_length_clause eq '-1');


  #### Build BIOSEQUENCE CATEGORY constraint
  my $biosequence_category_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"BPS.category",
    constraint_type=>"text_list",
    constraint_name=>"Biosequence Category",
    constraint_value=>$parameters{biosequence_category_constraint} );
  return if ($biosequence_category_clause eq '-1');


  #### Build TRANSMEMBRANE CLASS constraint
  my $transmembrane_class_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"BPS.transmembrane_class",
    constraint_type=>"text_list",
    constraint_name=>"Transmembrane Class",
    constraint_value=>$parameters{transmembrane_class_constraint} );
  return if ($transmembrane_class_clause eq '-1');


  #### Build NUMBER OF TRANSMEMBRANE REGIONS constraint
  my $n_transmembrane_regions_clause = $sbeams->parseConstraint2SQL(
    constraint_column=>"BPS.n_transmembrane_regions",
    constraint_type=>"flexible_int",
    constraint_name=>"Number of Transmembrane regions",
    constraint_value=>$parameters{n_transmembrane_regions_constraint} );
  return if ($n_transmembrane_regions_clause eq '-1');


  #### Build SORT ORDER
  my $order_by_clause = "";
  if ($parameters{sort_order}) {
    if ($parameters{sort_order} =~ /SELECT|TRUNCATE|DROP|DELETE|FROM|GRANT/i) {
      print "<H4>Cannot parse Sort Order!  Check syntax.</H4>\n\n";
      return;
    } else {
      $order_by_clause = " ORDER BY $parameters{sort_order}";
    }
  }


  #### Build ROWCOUNT constraint
  $parameters{row_limit} = 5000
    unless ($parameters{row_limit} > 0 && $parameters{row_limit}<=1000000);
  my $limit_clause = "TOP $parameters{row_limit}";


  #### Define some variables needed to build the query
  my $group_by_clause = "";
  my $final_group_by_clause = "";
  my @column_array;
  my $peptide_column = "";
  my $count_column = "";


  #### If the user opted to see the GO columns, add them in
  my @additional_columns = ();
  if ( $parameters{display_options} =~ /ShowGOColumns/ ||
       $molecular_function_clause.$biological_process_clause.
       $cellular_component_clause.$protein_domain_clause ) {
    @additional_columns = (
      ["molecular_function","MFA.annotation","Molecular Function"],
      ["molecular_function_GO","MFA.external_accession","molecular_function_GO"],
      ["biological_process","BPA.annotation","Biological Process"],
      ["biological_process_GO","BPA.external_accession","biological_process_GO"],
      ["cellular_component","CCA.annotation","Cellular Component"],
      ["cellular_component_GO","CCA.external_accession","cellular_component_GO"],
      ["interpro_protein_domain","IPDA.annotation","InterPro Protein Domain"],
      ["interpro_protein_domain_GO","IPDA.external_accession","interpro_protein_domain_GO"],
    );
  }

  #### If the user opted to see GO columns or provided some GO constraints,
  #### then join in the GO tables
  my $GO_join = "";
  if ( $parameters{display_options} =~ /ShowGOColumns/ ||
       $molecular_function_clause.$biological_process_clause.
       $cellular_component_clause.$protein_domain_clause ) {
    $GO_join = qq~
        LEFT JOIN BioLink.dbo.biosequence_annotated_gene AG
             ON ( BS.biosequence_id = AG.biosequence_id )
        LEFT JOIN BioLink.dbo.gene_annotation MFA
             ON ( AG.annotated_gene_id = MFA.annotated_gene_id
                   AND MFA.gene_annotation_type_id = 1 AND MFA.idx = 0 )
        LEFT JOIN BioLink.dbo.gene_annotation BPA
             ON ( AG.annotated_gene_id = BPA.annotated_gene_id
                   AND BPA.gene_annotation_type_id = 2 AND BPA.idx = 0 )
        LEFT JOIN BioLink.dbo.gene_annotation CCA
             ON ( AG.annotated_gene_id = CCA.annotated_gene_id
                   AND CCA.gene_annotation_type_id = 3 AND CCA.idx = 0 )
        LEFT JOIN BioLink.dbo.gene_annotation IPDA
             ON ( AG.annotated_gene_id = IPDA.annotated_gene_id
                   AND IPDA.gene_annotation_type_id = 4 AND IPDA.idx = 0 )
    ~;
  }


  #### Add in some extra columns if the user wants to see them
  if ( $parameters{display_options} =~ /ShowExtraProteinProps/ ) {
    @additional_columns = (
      #["fav_codon_frequency","STR(BS.fav_codon_frequency,10,3)","Favored Codon Frequency"],
      ["transmembrane_class","BPS.transmembrane_class","Transmembrane Regions Class"],
      ["n_transmembrane_regions","BPS.n_transmembrane_regions","Number of Transmembrane Regions"],
      ["isoelectric_point","STR(BPS.isoelectric_point,7,3)","pI"],
      ["has_signal_peptide","BPS.has_signal_peptide","Has Signal Peptide"],
      ["has_signal_peptide_probability","BPS.has_signal_peptide_probability","Has Signal Peptide Prob"],
      ["signal_peptide_length","BPS.signal_peptide_length","Signal Peptide Length"],
      ["signal_peptide_is_cleaved","BPS.signal_peptide_is_cleaved","Signal Peptide Is Cleaved"],
      ["protein_length","DATALENGTH(BS.biosequence_seq)","Protein Length"],
      ["category","BPS.category","Category"],
      ["transmembrane_topology","BPS.transmembrane_topology","Transmembrane Regions Topology"],
      ["chromosome","BPS.chromosome","Chromosome"],
      ["start_in_chromosome","BPS.start_in_chromosome","Start"],
      ["end_in_chromosome","BPS.end_in_chromosome","End"],
      @additional_columns,
    );
  }


  #### Define the desired columns in the query
  #### [friendly name used in url_cols,SQL,displayed column title]
  my @column_array = (
    ["biosequence_id","BS.biosequence_id","biosequence_id"],
    ["biosequence_set_id","BS.biosequence_set_id","biosequence_set_id"],
    ["set_tag","BSS.set_tag","set_tag"],
    ["biosequence_name","BS.biosequence_name","biosequence_name"],
    ["biosequence_gene_name","BS.biosequence_gene_name","gene_name"],
    ["accessor","DBX.accessor","accessor"],
    ["accessor_suffix","DBX.accessor_suffix","accessor_suffix"],
    ["biosequence_accession","BS.biosequence_accession","accession"],

    ["gene_symbol","BSA.gene_symbol","Annotated Gene Symbol"],
    ["full_gene_name","BSA.full_gene_name","Annotated Full Gene Name"],
    ["protein_EC_numbers","BSA.EC_numbers","Annotated EC Numbers"],
    ["biosequence_annotation_id","BSA.biosequence_annotation_id","biosequence_annotation_id"],
	["aliases","BSA.aliases","Aliases"],
	["duplicate_biosequences","BPS.duplicate_biosequences", "Duplicate Biosequences"],
	["functional_description","BSA.functional_description","Function"],
	["comment","BSA.comment","Comment"],
    ["last_annotated_by","BSAUL.username","Last Annotated By"],

    @additional_columns,
    ["biosequence_desc","BS.biosequence_desc","description"],
    ["biosequence_seq","BS.biosequence_seq","sequence"],
  );


  #### Adjust the columns definition based on user-selected options
  if ( $parameters{display_options} =~ /MaxSeqWidth/ ) {
    $max_widths{'biosequence_seq'} = 100;
  }
  if ( $parameters{display_options} =~ /NoSequence/ ) {
    pop(@column_array);
  }
  if ( $parameters{display_options} =~ /ShowSQL/ ) {
    $show_sql = 1;
  }


  #### Build the columns part of the SQL statement
  my %colnameidx = ();
  my @column_titles = ();
  my $columns_clause = $sbeams->build_SQL_columns_list(
    column_array_ref=>\@column_array,
    colnameidx_ref=>\%colnameidx,
    column_titles_ref=>\@column_titles
  );

  #### Define the SQL statement
  $sql = qq~
      SELECT $limit_clause $columns_clause
        FROM $TBPS_BIOSEQUENCE BS
        LEFT JOIN $TBPS_BIOSEQUENCE_SET BSS
             ON ( BS.biosequence_set_id = BSS.biosequence_set_id )
        LEFT JOIN $TB_DBXREF DBX ON ( BS.dbxref_id = DBX.dbxref_id )
        LEFT JOIN $TBPS_BIOSEQUENCE_PROPERTY_SET BPS
             ON ( BS.biosequence_id = BPS.biosequence_id )
        LEFT JOIN $TBPS_BIOSEQUENCE_ANNOTATION BSA
	     ON ( BS.biosequence_id = BSA.biosequence_id )
        LEFT JOIN $TB_USER_LOGIN BSAUL
	     ON ( BSA.modified_by_id = BSAUL.contact_id )
        $GO_join
       WHERE 1 = 1
      $biosequence_set_clause
	  $biosequence_clause
      $biosequence_name_clause
      $biosequence_accession_clause
      $biosequence_gene_name_clause
      $biosequence_seq_clause
      $biosequence_desc_clause
      $molecular_function_clause
      $biological_process_clause
      $cellular_component_clause
      $transmembrane_class_clause
      $n_transmembrane_regions_clause
      $protein_length_clause
      $biosequence_category_clause
      $order_by_clause
   ~;


  #### Certain types of actions should be passed to links
  my $pass_action = "QUERY";
  $pass_action = $apply_action if ($apply_action =~ /QUERY/i); 

  #### Define the hypertext links for columns that need them
  %url_cols = ('set_tag' => "$CGI_BASE_DIR/$SBEAMS_SUBDIR/ManageTable.cgi?TABLE_NAME=PS_biosequence_set&biosequence_set_id=\%$colnameidx{biosequence_set_id}V",
               'accession' => "\%$colnameidx{accessor}V\%$colnameidx{accesssion}V\%$colnameidx{accessor_suffix}V",

               'Annotated Full Gene Name' => "$CGI_BASE_DIR/$SBEAMS_PART/ManageTable.cgi?TABLE_NAME=PS_biosequence_annotation&biosequence_annotation_id=\%$colnameidx{biosequence_annotation_id}V&biosequence_id=\%$colnameidx{biosequence_id}V&ShowEntryForm=1",
	       'Annotated Full Gene Name_ATAG' => 'TARGET="Win1"',
	       'Annotated Full Gene Name_ISNULL' => ' [Add] ',
               'Annotated Gene Symbol' => "$CGI_BASE_DIR/$SBEAMS_PART/ManageTable.cgi?TABLE_NAME=PS_biosequence_annotation&biosequence_annotation_id=\%$colnameidx{biosequence_annotation_id}V&biosequence_id=\%$colnameidx{biosequence_id}V&ShowEntryForm=1",
	       'Annotated Gene Symbol_ATAG' => 'TARGET="Win1"',

               'Molecular Function' => "http://www.ebi.ac.uk/ego/QuickGO?mode=display&entry=\%$colnameidx{molecular_function_GO}V",
               'Molecular Function_ATAG' => 'TARGET="WinExt"',
               'Molecular Function_OPTIONS' => {semicolon_separated_list=>1},
               'Biological Process' => "http://www.ebi.ac.uk/ego/QuickGO?mode=display&entry=\%$colnameidx{biological_process_GO}V",
               'Biological Process_ATAG' => 'TARGET="WinExt"',
               'Biological Process_OPTIONS' => {semicolon_separated_list=>1},
               'Cellular Component' => "http://www.ebi.ac.uk/ego/QuickGO?mode=display&entry=\%$colnameidx{cellular_component_GO}V",
               'Cellular Component_ATAG' => 'TARGET="WinExt"',
               'Cellular Component_OPTIONS' => {semicolon_separated_list=>1},
               'InterPro Protein Domain' => "http://www.ebi.ac.uk/interpro/IEntry?ac=\%$colnameidx{interpro_protein_domain_GO}V",
               'InterPro Protein Domain_ATAG' => 'TARGET="WinExt"',
               'InterPro Protein Domain_OPTIONS' => {semicolon_separated_list=>1},
    );


  #### Define columns that should be hidden in the output table
  %hidden_cols = ('biosequence_set_id' => 1,
                  'biosequence_id' => 1,
                  'biosequence_annotation_id' => 1,
                  'accessor' => 1,
                  'accessor_suffix' => 1,
                  'molecular_function_GO' => 1,
                  'biological_process_GO' => 1,
                  'cellular_component_GO' => 1,
                  'interpro_protein_domain_GO' => 1,
   );



  #########################################################################
  #### If QUERY or VIEWRESULTSET was selected, display the data
  if ($apply_action =~ /QUERY/i || $apply_action eq "VIEWRESULTSET") {

    #### Show the SQL that will be or was executed
    $sbeams->display_sql(sql=>$sql) if ($show_sql);

    #### If the action contained QUERY, then fetch the results from
    #### the database
    if ($apply_action =~ /QUERY/i) {

      #### Fetch the results from the database server
      $sbeams->fetchResultSet(sql_query=>$sql,
        resultset_ref=>$resultset_ref);

      #### Store the resultset and parameters to disk resultset cache
      $rs_params{set_name} = "SETME";
      $sbeams->writeResultSet(resultset_file_ref=>\$rs_params{set_name},
        resultset_ref=>$resultset_ref,query_parameters_ref=>\%parameters);
    }


    #### If the output format is selected to be SequenceFormat
    if ( $parameters{display_options} =~ /SequenceFormat/ ) {
      displaySequenceView(
        resultset_ref=>$resultset_ref,
        label_peptide=>$label_peptide,
        label_start=>$label_start,
        label_end=>$label_end,
        url_cols_ref=>\%url_cols,
		display_mode=>$parameters{display_mode}
      );

    #### Otherwise display the resultset in conventional style
	}else {
      $sbeams->displayResultSet(rs_params_ref=>\%rs_params,
  	  url_cols_ref=>\%url_cols,hidden_cols_ref=>\%hidden_cols,
  	  max_widths=>\%max_widths,resultset_ref=>$resultset_ref,
  	  column_titles_ref=>\@column_titles,
          base_url=>$base_url,query_parameters_ref=>\%parameters,
      );

      #### Display the resultset controls
      $sbeams->displayResultSetControls(rs_params_ref=>\%rs_params,
        resultset_ref=>$resultset_ref,query_parameters_ref=>\%parameters,
        base_url=>$base_url
      );

      #### Display a plot of data from the resultset
      $sbeams->displayResultSetPlot(
        rs_params_ref=>\%rs_params,
        resultset_ref=>$resultset_ref,
        query_parameters_ref=>\%parameters,
        column_titles_ref=>\@column_titles,
        base_url=>$base_url,
      );


    }


    #### If a search_hit_id was supplied, give the user the option of
    #### updating the search_hit with a new protein
    my $nrows = @{$resultset_ref->{data_ref}};
    if ($search_hit_id && $nrows > 1) {
      print qq~
      	<FORM METHOD="post" ACTION="$PROGRAM_FILE_NAME"><BR><BR>
      	There are multiple proteins that contain this peptide.  If you
      	want to set a different protein as the preferred one, select it
      	from the list box below and click [UPDATE]<BR><BR>
      	<SELECT NAME="biosequence_id" SIZE=5>
      ~;

      my $biosequence_id_colindex =
        $resultset_ref->{column_hash_ref}->{biosequence_id};
      my $biosequence_name_colindex =
        $resultset_ref->{column_hash_ref}->{biosequence_name};
      foreach $element (@{$resultset_ref->{data_ref}}) {
        print "<OPTION VALUE=\"",$element->[$biosequence_id_colindex],"\">",
          $element->[$biosequence_name_colindex],"</OPTION>\n";
      }

      print qq~
      	</SELECT><BR><BR>
      	<INPUT TYPE="hidden" NAME="search_hit_id"
      	  VALUE="$search_hit_id">
      	&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
      	<INPUT TYPE="submit" NAME="apply_action" VALUE="UPDATE">
      	</FORM><BR><BR>
      ~;

    }


  #### If QUERY was not selected, then tell the user to enter some parameters
  } else {
    if ($sbeams->invocation_mode() eq 'http') {
      print "<H4>Select parameters above and press QUERY</H4>\n";
    } else {
      print "You need to supply some parameters to contrain the query\n";
    }
  }


} # end handle_request



###############################################################################
# evalSQL: Callback for translating global table variables to names
###############################################################################
sub evalSQL {
  my $sql = shift;

  return eval "\"$sql\"";

} # end evalSQL



###############################################################################
# displaySequenceView: Display the resultset in a FASTA-style format
###############################################################################
sub displaySequenceView {
  my %args = @_;
  my $SUB_NAME = 'displaySequenceView';


  #### Decode the argument list
  my $resultset_ref = $args{'resultset_ref'}
   || die "ERROR[$SUB_NAME]: resultset_ref not passed";
  my $label_peptide = $args{'label_peptide'} || '';
  my $label_start = $args{'label_start'} || '';
  my $label_end = $args{'label_end'} || '';

  #### Define the display mode
  my $mode = $args{'display_mode'} || 'x';


  #### Define standard variables
  my ($i,$element,$key,$value,$line,$result,$sql,$file);


  #### Get the hash of indices of the columns
  my %col = %{$resultset_ref->{column_hash_ref}};


  #### Get some information about the resultset
  my $data_ref = $resultset_ref->{data_ref};
  my $nrows = scalar(@{$data_ref});


  #### Define some variables
  my ($row,$pos);
  my ($biosequence_name,$description,$sequence,$seq_length,$tmr_topology,$tmr_class);
  my ($has_signal_peptide,$has_signal_peptide_probability,$signal_peptide_length,$signal_peptide_is_cleaved);
  my ($accessor,$accession);


  #### Display each row in the resultset
  foreach $row (@{$data_ref}) {
    #### Pull out data for this row into names variables
    $biosequence_name = $row->[$col{biosequence_name}];
    $description = $row->[$col{biosequence_desc}];
    $sequence = $row->[$col{biosequence_seq}];

    $accessor = $row->[$col{accessor}];
    $accession = $row->[$col{biosequence_accession}];
    $tmr_class = $row->[$col{transmembrane_class}];
    $tmr_topology = $row->[$col{transmembrane_topology}];
    $has_signal_peptide = $row->[$col{has_signal_peptide}];
    $has_signal_peptide_probability = $row->[$col{has_signal_peptide_probability}];
    $signal_peptide_length = $row->[$col{signal_peptide_length}];
    $signal_peptide_is_cleaved = $row->[$col{signal_peptide_is_cleaved}];


    #### Find all instances of the possibly-supplied peptide in the sequence
    my %start_positions;
    my %end_positions;
    if ($label_peptide) {
      my $pos = -1;
      while (($pos = index($sequence,$label_peptide,$pos)) > -1) {
        $start_positions{$pos} = 1;
        $end_positions{$pos+length($label_peptide)} = 1;
        $pos++;
      }
    }


    #### If the user supplied start and end positions to mark
    if ($label_start && $label_end) {
      my @starts = split(",",$label_start);
      foreach my $pos (@starts) {
        $start_positions{$pos-1} = 1;
      }
      my @ends = split(",",$label_end);
      foreach my $pos (@ends) {
        $end_positions{$pos-1} = 1;
      }
    }


    #### If we're in a label peptide mode, then set the width to 100 else 60
    my $page_width = 60;
    if ($label_peptide) {
      $page_width = 100;
    }

    #### If transmembrane regions topology has been supplied, find the TMRs
    my %tmr_start_positions;
    my %tmr_end_positions;
    my %tmr_color;
    my $notes_buffer = '';
    if ($tmr_topology) {
      $page_width = 100;
      my $start_side = substr($tmr_topology,0,1);
      my $tmp = substr($tmr_topology,1,9999);
      my @regions = split(/[io]/,$tmp);
      foreach my $region (@regions) {
        my ($start,$end) = split(/-/,$region);
        $tmr_start_positions{$start-1} = $start_side;
        $tmr_color{$start-1} = 'orange';
	if ($start_side eq 'i') {
          $start_side = 'o';
        } elsif ($start_side eq 'o') {
          $start_side = 'i';
        } else {
          $start_side = '?';
        }
        $tmr_end_positions{$end} = $start_side;
        $tmr_color{$end} = 'orange';
      }
      $notes_buffer .= "(Used TMR topology string: $tmr_topology)<BR>\n";
    }

    #### If there's a signal peptide, mark it as a blue
    if ($has_signal_peptide eq 'Y') {
      $tmr_start_positions{0} = '';
      $tmr_color{0} = 'blue';
      $tmr_end_positions{$signal_peptide_length} = '';
      $tmr_end_positions{$signal_peptide_length} = '/'
	if ($signal_peptide_is_cleaved eq 'Y');
      $tmr_color{$signal_peptide_length} = 'orange';
      $notes_buffer = "(signal peptide: Y, length: $signal_peptide_length, cleaved: $signal_peptide_is_cleaved, probability: $has_signal_peptide_probability)\n".$notes_buffer;
    }


    #### Write out a table of information
    unless ($mode eq 'FASTA') {
      print "<TABLE BORDER=0>\n";
      print "<TR><TD bgcolor=\"\#dddddd\"><BR>\n";

      my @display_columns = (
	{ 'Biosequence Name' => $biosequence_name },
	{ 'Biosequence Accession' => $accession },
        { 'Description' => $description },
      );

      foreach my $element ( @display_columns) {
	my ($key) = keys(%{$element});
	my $value = $element->{$key};
	print "$key: $value<BR>\n";
      }

      print "<BR></TD></TR>\n\n";
    }



    #### Write out the gene name and description
    unless ($mode eq 'FASTA') {
      print "<TR><TD bgcolor=\"\#eeeeee\"><PRE>\n&gt;<font color=\"blue\">";
    }

    if ($accessor && $accession && $mode ne 'FASTA') {
      print "<A HREF=\"$accessor$accession\">$biosequence_name</A>";
    } elsif ($mode eq 'FASTA') {
	  print "<PRE>&gt;$biosequence_name";
    } else {
	  print "$biosequence_name";
	}

    if ($mode eq 'FASTA') {
      print " $description</PRE>\n";
    } else {
      print "</font> <font color=\"purple\">$description</font>\n";
    }


    #### Write out the sequence in a pretty format, possibly labeled
    #### with a highlighted string of bases/residues
    my $offset = 0;
	if ($mode eq 'FASTA'){
	  print "<PRE>";
	}

    while (substr($sequence,$offset,60)) {
      print substr($sequence,$offset,60)."\n";
      $offset += 60;
    }
	  
	if ($mode eq 'FASTA'){
	  print "</PRE>\n";
	}

    unless ($mode eq 'FASTA') {

      print "<BR></PRE></TD></TR><TR><TD bgcolor=\"\#dddddd\"><PRE>";

      my $width_counter = 0;
      $seq_length = length($sequence);
      $i = 0;
      my $color_state = '';
      my $tmr_color = 'orange';
      while ($i < $seq_length) {

	my $trailing_flag = '';

	if (defined($end_positions{$i})) {
	  if ($color_state eq 'T+P') {
            print "</B></font><font color=\"$tmr_color\"><B>";
            $color_state = 'T';
          } else {
	    print "</B></font>";
            $color_state = '';
          }
	}

	if (defined($start_positions{$i})) {
	  if ($color_state eq 'T') {
            print "</B></font><font color=\"red\"><B>";
            $color_state = 'T+P';
          } else {
            print "<font color=\"#66DD00\"><B>";
            $color_state = 'P';
          }
	}

	if (defined($tmr_end_positions{$i})) {
	  if ($color_state eq 'T+P') {
	    print "($tmr_end_positions{$i})" if ($tmr_end_positions{$i});
            print "</B></font><font color=\"#66DD00\"><B>";
            $color_state = 'P';
          } elsif ($color_state eq 'T') {
	    print "($tmr_end_positions{$i})" if ($tmr_end_positions{$i});
	    print "</B></font>";
            $color_state = '';
          } else {
	    #### This must be a signal peptide misclassified as a TMR so ignore
	  }
	}

	if (defined($tmr_start_positions{$i})) {
	  $tmr_color = $tmr_color{$i};
	  if ($color_state eq 'P') {
            print "</B></font><font color=\"red\"><B>";
            $color_state = 'T+P';
  	    print "($tmr_start_positions{$i})" if ($tmr_start_positions{$i});
          } elsif ($color_state eq '') {
	    print "<font color=\"$tmr_color\"><B>";
            $color_state = 'T';
	    print "($tmr_start_positions{$i})" if ($tmr_start_positions{$i});
          } else {
	    #### This must be a signal peptide misclassified as a TMR so ignore
	  }
	}


        #if (substr($sequence,$i,1) eq 'K' || substr($sequence,$i,1) eq 'R') {
	#  print "<font color=\"green\"><B>".substr($sequence,$i,1).
        #    "</B></font>";
	#} else {
	  print substr($sequence,$i,1);
	#}
        $width_counter++;

        #### If we're in page_width=60 mode (FASTA format) then just
        #### do a line break every 60
        if ($page_width == 60) {
  	  if ($width_counter == $page_width) {
  	    print "\n";
            $width_counter = 0;
  	  }
        }

        #### If we're not in page_width=60 mode, then put spaces after
        #### tryptic cuts and break line at the first cut after 80
        if ($page_width != 60) {
          if (substr($sequence,$i,1) eq 'K' || substr($sequence,$i,1) eq 'R') {
            if ($width_counter > $page_width - 20) {
	      print "\n";
	      $width_counter = 0;
	    } else {
	      print " ";
              $width_counter++;
	    }
          }
        }

	$i++;

      }

      print "</B></font>" if ($end_positions{$i});
      print "</PRE>";

      #### Display the coloration legend
      print getSequenceColorLegend(have_topology => $col{transmembrane_topology});

      print "<BR><BR>Notes:<BR>\n$notes_buffer" if ($notes_buffer);
      print "<BR>To see full TMHMM result, copy the FASTA header and sequence above, and then <A HREF=\"http://www.cbs.dtu.dk/services/TMHMM/\" TARGET=\"TMHMM\">click here and paste the sequence</A>\n";

      print "</TD></TR>\n";
    }

  }


  if (0 == 1) {
    print "<TR><TD bgcolor=\"\#dddddd\"><PRE>";
    print getColorTestText();
    print "</PRE></TD></TR>\n";
  }


  unless ($mode eq 'FASTA') {
    print "</TABLE>\n";
  }

  return;

}


###############################################################################
# getSequenceColorLegend: Return the sequence coloration legend
###############################################################################
sub getSequenceColorLegend {
  my %args = @_;
  my $SUB_NAME = 'getSequenceColorLegend';

  #### Decode the argument list
  my $have_topology = $args{'have_topology'};


  my $buf = qq~<BR>
	- Referenced peptides are highlighted in <font color=\"green\">GREEN</font>.<BR>
	- Transmembrane regions (TMRs) are highlighted in <font color=\"orange\">ORANGE</font>.<BR>
  ~;

  if ($have_topology) {
    $buf .= qq ~<BR>
	- Signal peptides are highlighted in <font color=\"blue\">BLUE</font>.<BR>
	- Collisions in highlighting are shown in <font color=\"red\">RED</font>.<BR>
	- Internal ends of TMRs are labeled <font color=\"orange\">(i)</font> and external (outer) ends are labeled <font color=\"orange\">(o)</font>.<BR>
    ~;
  }

  return $buf;

}


###############################################################################
# getColorTestText: Return some text displaying various colors
###############################################################################
sub getColorTestText {
  my %args = @_;
  my $SUB_NAME = 'getColorTestText';

  my $buf = qq~<BR>
	COLOR CHECK:
	BLACK <B><font color=\"red\">AND RED</font></B> AND BLACK
	BLACK <B><font color=\"DeepPink\">AND HOTPINK</font></B> AND BLACK
	BLACK <B><font color=\"magenta\">AND MAGENTA</font></B> AND BLACK
	BLACK <B><font color=\"purple\">AND PURPLE</font></B> AND BLACK
	BLACK <B><font color=\"green\">AND GREEN</font></B> AND BLACK
	BLACK <B><font color=\"\#66DD00\">AND LAWNGREEN</font></B> AND BLACK
	BLACK <B><font color=\"SpringGreen\">AND SPRINGGREEN</font></B> AND BLACK
	BLACK <B><font color=\"yellow\">AND YELLOW</font></B> AND BLACK
	BLACK <B><font color=\"orange\">AND ORANGE</font></B> AND BLACK
	BLACK <B><font color=\"sienna\">AND SIENNA</font></B> AND BLACK
	BLACK <B><font color=\"black\">AND BLACK</font></B> AND BLACK
	BLACK <B><font color=\"blue\">AND BLUE</font></B> AND BLACK
	BLACK <B><font color=\"navy\">AND NAVY</font></B> AND BLACK
	BLACK <B><font color=\"turquoise\">AND TURQUOISE</font></B> AND BLACK
	BLACK <B><font color=\"cyan\">AND CYAN</font></B> AND BLACK
	BLACK <B><font color=\"gray\">AND GRAY</font></B> AND BLACK
  ~;

  return $buf;

}


