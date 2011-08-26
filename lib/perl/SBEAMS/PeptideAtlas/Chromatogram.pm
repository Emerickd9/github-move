package SBEAMS::PeptideAtlas::Chromatogram;

###############################################################################
# Class       : SBEAMS::PeptideAtlas::Chromatogram
# Author      : Terry Farrah <terry.farrah@systemsbiology.org>
#
=head1 SBEAMS::PeptideAtlas::Chromatogram

=head2 SYNOPSIS

  SBEAMS::PeptideAtlas::Chromatogram

=head2 DESCRIPTION

This is part of the SBEAMS::PeptideAtlas module which handles
things related to PeptideAtlas chromatograms

=cut
#
###############################################################################

use strict;
use vars qw($VERSION @ISA @EXPORT @EXPORT_OK);
require Exporter;
@ISA = qw();
$VERSION = q[$Id$];
@EXPORT_OK = qw();

use lib "/users/tfarrah/perl/lib";

use SBEAMS::Connection;
use SBEAMS::Connection::Tables;
use SBEAMS::Connection::Settings;
use SBEAMS::PeptideAtlas::Tables;


###############################################################################
# Global variables
###############################################################################
use vars qw($VERBOSE $TESTONLY $sbeams);


###############################################################################
# Constructor
###############################################################################
sub new {
    my $this = shift;
    my $class = ref($this) || $this;
    my $self = {};
    bless $self, $class;
    $VERBOSE = 0;
    $TESTONLY = 0;
    return($self);
} # end new


###############################################################################
# setSBEAMS: Receive the main SBEAMS object
###############################################################################
sub setSBEAMS {
    my $self = shift;
    $sbeams = shift;
    return($sbeams);
} # end setSBEAMS



###############################################################################
# getSBEAMS: Provide the main SBEAMS object
###############################################################################
sub getSBEAMS {
    my $self = shift;
    return $sbeams || SBEAMS::Connection->new();
} # end getSBEAMS



###############################################################################
# setTESTONLY: Set the current test mode
###############################################################################
sub setTESTONLY {
    my $self = shift;
    $TESTONLY = shift;
    return($TESTONLY);
} # end setTESTONLY



###############################################################################
# setVERBOSE: Set the verbosity level
###############################################################################
sub setVERBOSE {
    my $self = shift;
    $VERBOSE = shift;
    return($TESTONLY);
} # end setVERBOSE



###############################################################################
# getChromatogramParameters: given a chromatogram_id, get a bunch
#   of params relevant to the chromatogram and store in parameters
#   hash
###############################################################################
sub getChromatogramParameters{
  my $self = shift;
  my %args = @_;
  my $SEL_chromatogram_id = $args{SEL_chromatogram_id};
  my $param_href = $args{param_href};

  my $sql = qq~
    SELECT distinct
	   SELR.spectrum_filename,
	   SELE.data_path,
	   SELPI.stripped_peptide_sequence,
	   SELPI.modified_peptide_sequence,
	   SELPI.monoisotopic_peptide_mass,
	   SELPI.peptide_charge,
	   SELTG.q1_mz as targeted_calculated_q1_mz,
	   SELTG.collision_energy,
	   SELTG.retention_time,
	   SELTG.isotype,
	   SELTG.experiment_protein_name,
	   SELPG.m_score,
	   SELPG.Tr,
	   SELPG.max_apex_intensity,
	   SELTG.SEL_transition_group_id,
	   SELE.experiment_title,
	   SELPI.is_decoy,
	   SELPI.monoisotopic_peptide_mass,
	   SELPI.q1_mz as calculated_q1_mz
      FROM $TBAT_SEL_CHROMATOGRAM SELC
      JOIN $TBAT_SEL_TRANSITION_GROUP SELTG
	   ON ( SELTG.SEL_transition_group_id = SELC.SEL_transition_group_id )
      LEFT JOIN $TBAT_SEL_PEAK_GROUP SELPG
	   ON ( SELPG.SEL_chromatogram_id = SELC.SEL_chromatogram_id )
      LEFT JOIN $TBAT_SEL_PEPTIDE_ION SELPI
	   ON ( SELPI.SEL_peptide_ion_id = SELTG.SEL_peptide_ion_id )
      JOIN $TBAT_SEL_RUN SELR
	   ON ( SELR.SEL_run_id = SELTG.SEL_run_id )
      JOIN $TBAT_SEL_EXPERIMENT SELE
	   ON ( SELE.SEL_experiment_id = SELR.SEL_experiment_id )
     WHERE SELC.SEL_chromatogram_id = '$SEL_chromatogram_id'
     ;
  ~;
  #print "$sql<br>\n";
  my @rows = $sbeams->selectSeveralColumns( $sql );
  my $n_rows = scalar @rows;
  print "<P>ERROR: nothing returned for chromatogram_id $param_href->{'SEL_chromatogram_id'}.</P>\n"
     if ($n_rows == 0 );
  print "<P>WARNING: $n_rows rows of data returned for chromatogram $param_href->{'SEL_chromatogram_id'}! Only considering first.</P>\n"
     if ($n_rows > 1);
  my $results_aref = $rows[0];

  $param_href->{'spectrum_basename'} = $results_aref->[0];
  $param_href->{'spectrum_pathname'} = $results_aref->[1].'/'.$results_aref->[0];
  $param_href->{'pepseq'} = $results_aref->[2];
  $param_href->{'modified_pepseq'} = $results_aref->[3];
  $param_href->{'precursor_neutral_mass'} = $results_aref->[4];
  $param_href->{'precursor_charge'} = $results_aref->[5];
  $param_href->{'q1'} = $results_aref->[6];
  $param_href->{'ce'} = $results_aref->[7];
  $param_href->{'rt'} = $results_aref->[8] || 0;
  $param_href->{'isotype'} = $results_aref->[9];
  $param_href->{'protein_name'} = $results_aref->[10];
  $param_href->{'m_score'} = $results_aref->[11];
  $param_href->{'Tr'} = $results_aref->[12];
  $param_href->{'max_apex_intensity'} = $results_aref->[13];
  my $transition_group_id = $results_aref->[14];
  $param_href->{'transition_info'} =
      getTransitionInfo($transition_group_id);
  $param_href->{'experiment_title'} = $results_aref->[15];
  $param_href->{'is_decoy'} = $results_aref->[16];
  $param_href->{'monoisotopic_peptide_mass'} = $results_aref->[17];
  $param_href->{'calculated_q1'} = $results_aref->[18];

      # Create a string describing this transition group.
      sub getTransitionInfo {
        my $transition_group_id = shift;
        my $sql = qq~
          SELECT q3_mz, frg_type, frg_nr, frg_z, relative_intensity
            FROM $TBAT_SEL_TRANSITION
           WHERE SEL_transition_group_id = '$transition_group_id'
        ~;
	my @rows = $sbeams->selectSeveralColumns($sql);
        my $string = "";
        for my $row (@rows) {
          $string .= "$row->[0],$row->[1]$row->[2]+$row->[3],$row->[4],";
        }
        return $string;
      }

}

###############################################################################
# getNewChromatogramFilename
#   Create descriptive filename for chromatogram incorporating
#   timestamp
###############################################################################
sub getNewChromatogramFilename {
  my $self = shift;
  my %args = @_;
  my $spectrum_basename = $args{spectrum_basename};
  my $pepseq = $args{pepseq};

  my ($sec,$min,$hour,$mday,$mon,$year,$wday, $yday,$isdst)=localtime(time);
  my $timestamp = sprintf "%1d%02d%02d%02d%02d%02d-%02d",
     $year-110,$mon+1,$mday,$hour,$min,$sec,int(rand(100));
  my $chromgram_basename = "${spectrum_basename}_${pepseq}_${timestamp}";
  return $chromgram_basename;
}

###############################################################################
# writeJsonFile
###############################################################################
sub writeJsonFile {
  my $self = shift;
  my %args = @_;
  my $json_string = $args{json_string};
  my $json_physical_pathname = $args{json_physical_pathname};

  open (JSON, ">$json_physical_pathname") ||
    die "writeJsonFile: can't open $json_physical_pathname for writing";
  print JSON $json_string;
  close JSON;
}

###############################################################################
# mzML2json - Create a .json string representing a given chromatogram
###############################################################################
sub mzML2json {
  my $self = shift;
  my %args = @_;
  my $param_href = $args{param_href};    # describes desired chromatogram

  my $rt = $param_href->{rt} || $param_href->{Tr} || 0;
  my $target_q1 = $param_href->{q1};
  my $tx_info = $param_href->{transition_info};

  my $count = 0;
  my $tol = 0.005;

  # Read scans for $q1 into a hash
  my $traces_href = mzML2traces(
    spectrum_pathname => $param_href->{spectrum_pathname},
    target_q1 => $target_q1,
    tol => $tol,
    tx_info => $tx_info,
  );

  # Unpack and store the transition info string, if provided
	store_tx_info_in_traces_hash (
		tx_info => $tx_info,
		traces_href => $traces_href,
	) if ($tx_info);

  # Create and return .json string.
  return traces2json(
		traces_href => $traces_href,
    rt => $rt,
    tx_info => $tx_info,
  );
}

###############################################################################
# mzXML2json - Create a .json string representing a given chromatogram
###############################################################################
sub mzXML2json {
  my $self = shift;
  my %args = @_;
  my $param_href = $args{param_href};    # describes desired chromatogram

  my $rt = $param_href->{rt} || $param_href->{Tr} || 0;
  my $target_q1 = $param_href->{q1};
  my $tx_info = $param_href->{transition_info};

  my $count = 0;
  my $tol = 0.005;

  # Read scans for $q1 into a hash
  my $traces_href = mzXML2traces(
    spectrum_pathname => $param_href->{spectrum_pathname},
    target_q1 => $target_q1,
    tol => $tol,
    tx_info => $tx_info,
  );
  my %traces = %{$traces_href};

  # Unpack and store the transition info string, if provided
  if ($tx_info) {
    store_tx_info_in_traces_hash (
      tx_info => $tx_info,
      traces_href => \%traces,
    );
  }

  # Create .json string.
  my $json_string = traces2json(
    traces_href => \%traces,
    rt => $rt,
    tx_info => $tx_info,
  );
  return $json_string;
}

###############################################################################
# mzML2traces
# Read the chromatograms for a particular Q1 from an mzML file and store
# the time & intensity information in a hash.
###############################################################################
sub mzML2traces {

	use XML::TreeBuilder;
	use XML::Writer; 

	my %args = @_;
	my $spectrum_pathname = $args{spectrum_pathname};
	my $target_q1 = $args{target_q1};
	my $tol = $args{tol};
	my $tx_info = $args{tx_info};

	my %traces;

	my $mzMLtree    = XML::TreeBuilder->new();
	$mzMLtree->parse_file($spectrum_pathname) || die
	"Couldn't parse $spectrum_pathname";
	my @allcgrams = $mzMLtree->find_by_tag_name('chromatogram');
	my @alloffsets = $mzMLtree->find_by_tag_name('offset');
	my $ncgrams = scalar (@allcgrams);
	my $noffsets = scalar (@alloffsets);

	for my $cgram (@allcgrams) {
		#my $index = $cgram->attr('index');
		#$verbose && print "Processing chromatogram $index\n";
		my $id = $cgram->attr('id');
		my ($q1, $q3, $sample, $period, $experiment, $transition,);
		# If this is a parsable chromatogram ID, get its infos
		if (($id =~
				/.*SRM.*\s+Q1=(\S+)\s+Q3=(\S+)\s+sample=(\S+)\s+period=(\S+)\s+experiment=(\S+)\s+transition=(\S+)/) #QTRAP data from Cima and Ralph Scheiss
			||
			($id =~ /SRM SIC (\S+),(\S+)/) )   #TSQ data from Nathalie
		{
			$q1 = $1;
			$q3 = $2;
			$sample = $3;
			$period = $4;
			$experiment = $5;
			$transition = $6;

			# If this is our target Q1 ...
			if (($q1 <= $target_q1+$tol) && ($q1 >= $target_q1-$tol)) {
				my @binaryDataArrayLists =
				$cgram->find_by_tag_name('binaryDataArrayList');

				my $n = scalar @binaryDataArrayLists;
				my @binaryDataArrays =
				$binaryDataArrayLists[0]->find_by_tag_name('binaryDataArray');
				$n = scalar @binaryDataArrays;


				my ($n_time, $n_int, $time_aref, $int_aref);

				#Get times
				my @binary = $binaryDataArrays[0]->find_by_tag_name('binary');
				$n = scalar @binary;
				if (defined $binary[0]->content) {
					$time_aref = decode_mzMLtimeArray($binary[0]->content->[0]);
					$n_time = scalar @{$time_aref};
					for (my $i=0; $i<$n_time; $i++) {
					}
				} else {
					$n_time = 0;
				}

				#Get intensities
				@binary = $binaryDataArrays[1]->find_by_tag_name('binary');
				$n = scalar @binary;
				if (defined $binary[0]->content) {
					$int_aref = decode_mzMLintensityArray($binary[0]->content->[0]);
					$n_int = scalar @{$int_aref};
					for (my $i=0; $i<$n_int; $i++) {
					}
				} else {
					$n_int = 0;
				}

				die "$n_time timepoints, $n_int intensities!" if ($n_time != $n_int);

				# Store info in traces hash
				for (my $i=0; $i<$n_time; $i++) {
					my $time = $time_aref->[$i];
					my $intensity = $int_aref->[$i];
					$traces{$q1}->{$q3}->{'rt'}->{$time} = $intensity;
					$traces{$q1}->{$q3}->{'q1'} = $q1;
					$traces{$q1}->{$q3}->{'eri'} = 0.01 if $tx_info;
				}

			} # end if target Q1
		} # end if parsable chromatogram ID
	} # end for each chromatogram

	return (\%traces);
}

###############################################################################
# mzXML2traces
# Read the scans for a particular Q1 from an mzXML file and store
# the time & intensity information in a hash.
###############################################################################

sub mzXML2traces {
  my %args = @_;
  my $spectrum_pathname = $args{spectrum_pathname};
  my $target_q1 = $args{target_q1};
  my $tol = $args{tol};
  my $tx_info = $args{tx_info};

  my ($scan, $time, $q1, $q3, $intensity);
  my (%traces, $intensity_aref);
  open (MZXML, $spectrum_pathname);
  #open (MZXML, $param_href->{spectrum_pathname});
  while (my $line = <MZXML>) {
    # New scan. Store data from previous.
    if ($line =~ /<scan num="(\d+)"/) {
      $scan = $1;
      # maybe need to check when scans start at 0
      #print "Q1: $q1\n";
      if (($scan > 1) &&
	  ($q1 <= $target_q1+$tol) && ($q1 >= $target_q1-$tol)) {
	if ($intensity_aref) {
	  my @intensities = @{$intensity_aref};
	  while (@intensities) {
	    my $q3 = shift @intensities;
	    my $intensity = shift @intensities;
	    $traces{$q1}->{$q3}->{'rt'}->{$time} = $intensity;
	    $traces{$q1}->{$q3}->{'q1'} = $q1;
	    # initialize eri to a tiny value in case we don't get a value
	    $traces{$q1}->{$q3}->{'eri'} = 0.1 if $tx_info;
	    #print "$q1\t$q3\t$time\t$intensity\n";
	  }
	} else {
	  $traces{$q1}->{$q3}->{'rt'}->{$time} = $intensity;
	  $traces{$q1}->{$q3}->{'q1'} = $q1;
	  $traces{$q1}->{$q3}->{'eri'} = 0.01 if $tx_info;
	  #print "$q1\t$q3\t$time\t$intensity\n";
	}
	undef $intensity_aref;
      }
      # Data for current scan.
    } elsif ($line =~ /retentionTime="PT(\S+)(\w)"/) {
      # Report RT in seconds.
      # Complete parser of this element, type="xs:duration",
      # would be more complicated.
      my $n = $1;
      my $units = $2;
      # NOTE: most/all of the sprintf field width specifiers below are useless
      # because the whitespace gets lost via the javascript.
      $time = sprintf ("%0.3f", ($units eq 'M') ? $n*60 : $n );
    } elsif ($line =~ /basePeakIntensity="(\S*?)"/) {
      $intensity = $1;
    } elsif ($line =~ /basePeakMz="(\S*?)"/) {
      $q3 = $1;
      # sometimes, multiple peaks are encoded in a single <scan>
    } elsif ($line =~ /compressedLen.*\>(.+)\<.peaks>/) {
      #print $1, "\n";
      $intensity_aref = decode_mzXMLScan($1);
      #for my $elt (@{$intensity_aref}) { print "$elt\n"; }
    } elsif ($line =~ /<precursorMz.*>(\S+)<.precursorMz>/) {
      $q1 = $1;
    }
  }
  close MZXML;
  return (\%traces);
}


###############################################################################
# traces2json
# Given a hash containing time & intensity information for a Q1,
#  write a json data object suitable for Chromavis.
###############################################################################
sub traces2json {
  my %args = @_;
  my $traces_href = $args{traces_href};
  my %traces = %{$traces_href};
  my $rt = $args{rt};
  my $tx_info = $args{tx_info};

  my $json_string = '{';

  # Open data_json element
  $json_string .= "data_json : [\n";

  my $count = 0;
  for my $q1 ( sort { $a <=> $b } keys %traces) {
    for my $q3 ( sort { $a <=> $b } keys %{$traces{$q1}}) {
      $count++;
      $json_string .= sprintf "  {  full : 'COUNT: %2.2d Q1:%0.3f Q3:%0.3f',\n", $count, $traces{$q1}->{$q3}->{'q1'}, $q3;
      my $label = '';
      if ($tx_info) {
	$label .= sprintf "%-5s ", $traces{$q1}->{$q3}->{frg_ion};
      } else {
	$label .= sprintf "%3.3d ", $count;
      }


      $label .=  sprintf "%7.3f / %7.3f",  $traces{$q1}->{$q3}->{'q1'}, $q3;
      $label .= sprintf " ERI: %0.1f", $traces{$q1}->{$q3}->{eri},
      if ($traces{$q1}->{$q3}->{eri});
      $json_string .= "    label : '$label',\n";
      $json_string .= "      eri : $traces{$q1}->{$q3}->{eri},\n" if ($traces{$q1}->{$q3}->{eri});
      $json_string .= "     data : [\n";
      # Write each pair of numbers in Dick's JSON format.
      for my $time (sort {$a <=> $b} keys %{$traces{$q1}->{$q3}->{'rt'}}) {
	my $intensity = $traces{$q1}->{$q3}->{'rt'}->{$time};
	$json_string .= sprintf "          {time : %0.4f, intensity : %0.5f},\n", $time/60, $intensity;
      }
      # Close this chromatogram in JSON object
      $json_string .= "        ]},\n";
    }
  }
  # Close data_json
  $json_string .= "]\n";

  # Write the retention time marker, if value provided
  if ($rt )  {
    my $formatted_rt = sprintf "%0.3f", $rt;
    $json_string .= ", vmarker_json : [ {id : '$formatted_rt', value : $rt} ]\n";
  } else {
    $json_string .= ", vmarker_json : [  ]\n";
  }
  $json_string .= "}\n";
  return $json_string;
}

###############################################################################
# store_tx_info_in_traces_hash
#   Given a string containing Q3,frg_ion,intensity triplets, store
#   this info in the portion of the traces hash for this Q3
###############################################################################
sub store_tx_info_in_traces_hash {
  my %args = @_;
  my $tx_info = $args{tx_info};
  my $traces_href = $args{traces_href};
  my %traces = %{$traces_href};

  my %tx_info_values;
  my $tol = 0.0005;
  my @values = split(",",$tx_info);
  while (@values) {
    # get a q3, fragment ion, expected intensity triplet
    my $q3 = shift @values;
    my $frg_ion = shift @values;
    my $int = shift @values;
    # see if we have data for this q3
    for my $data_q1 (keys %traces) {
      # initialize eri to a small number in case we don't find it.
      for my $data_q3 (keys %{$traces{$data_q1}}) {
	if (($q3 <= $data_q3+$tol) && ($q3 >= $data_q3-$tol)) {
	  # if we do, store the fragment ion and the eri
	  $traces{$data_q1}->{$data_q3}->{'frg_ion'} = $frg_ion;
	  $traces{$data_q1}->{$data_q3}->{'eri'} = $int;
	  last;
	}
      }
    }
  }
}

###############################################################################
# decode_mzMLtimeArray
# A 64-bit base 64 string encodes a list of time values. Return that list.
###############################################################################

sub decode_mzMLtimeArray {
  my $base64_string = shift ||
    die ("decode_mzMLtimeArray: no argument");
  #my $decoded = Base64::b64decode($base64_string);
	my $decoded = decode_base64($base64_string);
	my $swapped = $decoded;
	# $swapped = byteSwap($decoded, 64);  #don't need to swap
  my @array = unpack("d*", $swapped);
  return \@array;
}

###############################################################################
# decode_mzMLintensityArray
# A 32-bit base 64 string encodes a list of intensity values. Return that list.
###############################################################################

sub decode_mzMLintensityArray {
  my $base64_string = shift ||
     die ("decode_mzMLintensityArray: no argument");
  #my $decoded = Base64::b64decode($base64_string);
	my $decoded = decode_base64($base64_string);
	my $swapped = $decoded;
	# $swapped = byteSwap($decoded, 32);  #don't need to swap
  my @array = unpack("f*", $swapped);
  return \@array;
}

###############################################################################
# decode_mzXMLScan
# A base 64 string encodes a list of q3, intensity pairs. Return that list.
###############################################################################

sub decode_mzXMLScan {
  my $base64_string = shift || die ("decode_mzXMLScan: no argument");
  my $decoded = decode_base64($base64_string);
  my @array = unpack("f*", byteSwap($decoded));
  return \@array;
}

###############################################################################
# byteSwap: Exchange the order of each pair of bytes in a string.
###############################################################################
sub byteSwap {
  my $in = shift || die("byteSwap: no input");

  my $out = '';
  for (my $i = 0; $i < length($in); $i+=4) {
    $out .= reverse(substr($in,$i,4));
  }
  return($out);
}

###############################################################################
# mzML2json - Create a .json file representing a given chromatogram
#   This makes use of the ATAQS peptideChromatogramExtractor, but
#   it is slow and it wasn't working for PASSEL for unknown reasons.
#    08/23/11: DEPRECATED, because it's slow to call out.
###############################################################################
sub mzML2json_using_PCE {

  my $self = shift;
  my %args = @_;
  my $param_href = $args{param_href};
  my $physical_tmp_dir = $args{physical_tmp_dir};
  my $chromgram_basename = $args{chromgram_basename};

  my ($ion, $ion_charge, $pepseq, $spectrum_pathname,
	$ce, $rt, $delta_rt, $fragmentor, $precursor_neutral_mass);

  $precursor_neutral_mass = $param_href->{'precursor_neutral_mass'};
  $spectrum_pathname = $param_href->{'spectrum_pathname'};
  $pepseq = $param_href->{'pepseq'};
  $ce = $param_href->{'ce'} || 99;
  $rt = $param_href->{'rt'} || $param_href->{'Tr'} || 99;
  $delta_rt = $param_href->{'delta_rt'} || 99 ;
  $fragmentor = $param_href->{'fragmentor'} || 125;

  # Get charge 2, 3 Q1 values for this peptide.
  my $q1_charge3 = $precursor_neutral_mass / 3 + 1.00727638;
  my $q1_charge2 = $precursor_neutral_mass / 2 + 1.00727638;

  # Get the Q3 for all transitions for this peptide. 
  # Open mzML file for reading
  open(MZML, $spectrum_pathname) || print "<p>Can't open mzML file $spectrum_pathname.</p>\n";

  my $line;
  # Look for <index name="chromatogram"
  while ($line = <MZML>) {
    last if ($line =~ /<index name="chromatogram"/);
  }
  # Look for Q1=xxxxx Q3=xxxx
  # If Q1 within 0.01 of desired, save exact value plus Q3 value
  my $q3;
  my (@q1_list, @q3_list, @charge_list);
  my $tolerance = 0.01;
  while ($line = <MZML>) {
    if ($line =~ /Q1=(\S+) Q3=(\S+)/) {
      my $this_q1 = $1; my $this_q3 = $2;
      # CLEANUP
      if (abs($this_q1-$q1_charge2) < $tolerance) {
	push (@q1_list, $this_q1);
	push (@q3_list, $this_q3);
	push (@charge_list, 2);
      } elsif (abs($this_q1-$q1_charge3) < $tolerance) {
	push (@q1_list, $this_q1);
	push (@q3_list, $this_q3);
	push (@charge_list, 3);
      }
    }
  }
  close MZML;
#
  # Now, make the .tsv file for PeptideChromatogramExtractor.
  # Standard ATAQS format.
  my $tsv_pathname = "$physical_tmp_dir/$chromgram_basename.tsv";
  # For some reason, I can't write to tmp, only to images/tmp.
  # Hmmph!
  open (TSV, ">$tsv_pathname") || print "<p>Can't open $tsv_pathname for writing!</p>\n";
  print TSV "Dynamic MRM\n";
  print TSV "Compound Name\tISTD?\tPrecursor Ion\tMS1 Res\tProduct Ion\tMS2 Res\tFragmentor\tCollision Energy\tRet Time (min)\tDelta Ret Time\tPolarity\n";

  # Trick PeptideChromatogramExtractor to put traces for all charges
  # into a single .txt file, by including the same charge digit in all
  # pepnames. Might be better to change ataqs2json to combine several
  # .txt files into one .json file. CLEANUP.
  my $first_charge = $charge_list[0];
  for my $q1 (@q1_list) {
    my $q3 = shift @q3_list;
    my $charge = shift @charge_list;
    # $ion and $ion_charge are currently bogus, but they are needed for the
    # pepname syntax
    $ion = "y1"; $ion_charge = "1";
    my $pepname = $pepseq . "." . $first_charge . $ion . "-" .$ion_charge;
    print TSV "$pepname\t".
	      "FALSE\t".
	      "$q1\t".
	      "Wide\t".
	      "$q3\t".
	      "Unit\t".
	      "$fragmentor\t".
	      "$ce\t".
	      "$rt\t".
	      "$delta_rt\t".
	      "Positive\n";
     # In case multiple traces per charge, increment ion_charge to
     # allow unique pepnames
     $ion_charge++;
  }
  close TSV;
  print "<!-- TSV pathname: $tsv_pathname -->\n";

  # Now! run the java program to extract the traces for the
  # transitions described in the .tsv file and store in a .txt file
  my ${pa_java_home} = "$PHYSICAL_BASE_DIR/lib/java/SBEAMS/SRM";
  my $user = $chromgram_basename;
  my $java_wrapper =
    "${pa_java_home}/PeptideChromatogramExtractor.sh ".
    "$tsv_pathname $spectrum_pathname $user $rt";

  my $shell_result = `pwd 2>&1`;
  print "<!-- Current working directory: $shell_result -->\n";
  print "<!-- Running Java wrapper: $java_wrapper -->\n";
  my $shell_result = `$java_wrapper 2>&1`;
  # This does not seem to be printing the errors.
  print "<!-- Java wrapper result: $shell_result -->\n";

  # Convert the .txt file into a .json files for chromatogram viewer,
  # then delete it. (Original early 2011 code handled multiple files;
  # when would we ever have multiple files? "One for each distinct
  # mod_pep and charge combo", it says in wrapper script.)
  my @txt_files = split (" ",  `ls ${pa_java_home}/$user*.txt`);
  if ((scalar @txt_files) > 1) {
    print "<!-- Warning: multiple files ${pa_java_home}/${user}*.txt -->\n";
  } elsif ((scalar @txt_files) < 1) {
    die "mzML2json(): No files match ${pa_java_home}/${user}*.txt";
  }
  my $pce_txt_file = $txt_files[0];
  print "<!-- Converting $pce_txt_file to json -->\n";
  my $json_string = $self->PCEtxt2json (
    rt => $rt,
    pce_txt_file => $pce_txt_file,
  );
  `rm -f $pce_txt_file`;
#
  my $json_string;
  return $json_string;
}


###############################################################################
# PCEtxt2json - convert PeptideChromatogramExtractor .txt files to .json
###############################################################################
sub PCEtxt2json {

  my $self = shift;
  my %args = @_;
  my $rt = $args{rt};
  my $target_q1 = $args{target_q1};
  my $tx_info = $args{tx_info};
  my $pce_txt_file = $args{pce_txt_file};

  use MIME::Base64;

#--------------------------------------------------
# a JSON object for the chromatogram,
#  is simply one or more lists (named "data") of (time, intensity)
#   (or, for RT marker, (id, value)) pairs:
#      var data_json = [
#        { full : 'Q1:590.337 Q3:385.22 Z1:3 Z3:1 CE:16.5 ION:y3',
#         label : '$num Q1:590.337 Q3:385.22',
#           data : [{time : 2898.333, intensity : 40.166},
#                   {time : 3056.667, intensity : -0.052}, ...
#                   {id : 'Retention Time', value : 1200}, ...
#                  ]},
#          ...
#-------------------------------------------------- 

  open (TXT, $pce_txt_file) ||
     die "PCEtxt2json: can't open $pce_txt_file for reading.";
  my $json_string = "{";

# Open data_json element
  $json_string .= "data_json : [\n";

  my $count = 0;

  while (my $line = <TXT>) {
    # First line in Mi-Youn's text file has some infos: read them.
    chomp $line;
    $line =~ /Q1:(\S+) Q3:(\S+) Z1:(\S+) Z3:(\S+) CE:(\S+) ION:(\S+)/;
    my ($q1, $q3, $z1, $z3, $ce, $ion) = ($1, $2, $3, $4, $5, $6);
    $count++;

    # Read next input line.
    $line = <TXT>;
    # Strip punctuation from input line. What's left is a list of numbers.
    $line =~ s/\(//g;
    $line =~ s/\)//g;
    $line =~ s/,//g;
    my @numbers = split(' ', $line);

    # Open this chromatogram in JSON object
    $json_string .= "  {  full : 'COUNT: $count Q1:$q1 Q3:$q3 Z1:$z1 Z3:$z3 CE:$ce ION:$ion',\n";
    #my $label = "ION:$ion";
    my $label =  sprintf "%3d  Q1:$q1 Q3:$q3", $count;
    $json_string .= "    label : '$label',\n";
    $json_string .= "     data : [\n";

    # Write each pair of numbers in Dick's JSON format.
    while (@numbers) {
      my $time = shift @numbers;
      my $intensity = shift @numbers;
      $json_string .= "          {time : $time, intensity : $intensity},\n";
    }
    # TO DO : strip final comma, says Dick.

    # Close this chromatogram in JSON object
    $json_string .= "        ]},\n";
    # TO DO : strip final comma, says Dick.
  }
  close TXT;

# Close data_json
  $json_string .= "]\n";

# Write the retention time marker, if value provided
  if ($rt )  {
    my $formatted_rt = sprintf "%0.3f", $rt;
    $json_string .= ", vmarker_json : [ {id : '$formatted_rt', value : $rt} ]\n";
  } else {
    $json_string .= ", vmarker_json : [  ]\n";
  }
  $json_string .= "}\n";
  return $json_string;
}

###############################################################################
# getTopHTMLforChromatogramViewer
###############################################################################
sub getTopHTMLforChromatogramViewer {

  my $self = shift;
  my %args = @_;
  my $param_href = $args{param_href};
  my $seq = $args{seq};
  my $precursor_neutral_mass = $args{precursor_neutral_mass};
  my $precursor_charge = $args{precursor_charge};
  my $spectrum_pathname = $args{spectrum_pathname};

  # we are not using this anymore b/c we have stored monois. pep mass07/08/11
  my $precursor_neutral_mass_s = sprintf "%0.3f", $precursor_neutral_mass;
  my $precursor_rt = $param_href->{rt};
  my $best_peak_group_rt = $param_href->{Tr};
  my $m_score = $param_href->{m_score};
  my $top_html = "<p><big>";
  $top_html .= " DECOY" if $param_href->{is_decoy} eq 'Y';
  $top_html .= " <b>$seq</b></big> ";
  if ($param_href->{monoisotopic_peptide_mass}) {
    my $mpm_s = sprintf "%0.3f", $param_href->{monoisotopic_peptide_mass};
    $top_html .= "($mpm_s Daltons) </b>\n";
  }
  $top_html .= "<b><big>+$precursor_charge, $param_href->{isotype}</big></b>\n";
  $top_html .= "<br><b>Experiment: </b> $param_href->{experiment_title}\n"
     if $param_href->{experiment_title};
  $top_html .= "<br><b>Spectrum file:</b> $spectrum_pathname\n";
  if ($precursor_rt) {
    $precursor_rt = sprintf "%0.3f", ${precursor_rt}/60;
    $top_html .= "<br>Precursor RT\: $precursor_rt\n";
  }
  if ($m_score) {
    $top_html .= "<br><b>mProphet:</b> ";
    if ($best_peak_group_rt) {
      my $best_peak_group_rt_s = sprintf "%0.3f", ${best_peak_group_rt}/60;
      $top_html .= "best peakgroup RT = $best_peak_group_rt_s, "
    }
    my $m_score_s = sprintf "%0.3f", $m_score;
    $top_html .= "m_score = $m_score_s\n";
  }
  return $top_html;
}

###############################################################################
# readJsonChromatogramIntoResultsetHash -
#   read json object into array. Store array plus
#   list of column headers in a hash of format expected by writeResultSet.
#   Simple-minded parsing assumes that each time/intensity pair has own line.
###############################################################################
sub readJsonChromatogramIntoResultsetHash {

  my $self = shift;
  my %args = @_;
  my $param_href = $args{param_href};
  my $json_physical_pathname = $args{json_physical_pathname};
  my %dataset;
  my @chromatogram_array = ();

  open (JSON, $json_physical_pathname) ||
      die "Can't open .json file $json_physical_pathname";
  my ($trace_num, $time, $q1, $q3, $intensity);
  $trace_num = 0;
  while (my $line = <JSON>) {
    chomp $line;
    #print "<br>$line\n";
    if ($line =~ /full/ ) {
      $trace_num++;
    }
    if ($line =~ /Q1:(\d+\.\d+)/ ) {
      $q1 = $1;
    }
    if ($line =~ /Q3:(\d+\.\d+)/ ) {
      $q3 = $1;
    }
    if ($line =~ /\{\s*time\s*:\s*(\d+\.\d+),\s*intensity\s*:\s*(\d+\.\d+)\s*\}/) {
      $time = $1; $intensity = $2;
      push (@chromatogram_array, [$trace_num, $time, $q1, $q3, $intensity]);
      #print "<br>$time $q3 $intensity<br>\n";
    }
  }
  $dataset{data_ref} = \@chromatogram_array;
  $dataset{column_list_ref} =
      ['trace_num', 'seconds', 'Q1', 'Q3', 'intensity'];
  return \%dataset;
}

###############################################################################
# getBottomHTMLforChromatogramViewer
###############################################################################
sub getBottomHTMLforChromatogramViewer {

  my $self = shift;
  my %args = @_;
  my $param_href = $args{param_href};
  my $rs_set_name = $args{rs_set_name};

  my $bottom_html =  qq~
  <BR>Download chromatogram in Format: 
  <a href="$CGI_BASE_DIR/GetResultSet.cgi/$rs_set_name.tsv?rs_set_name=$rs_set_name&format=tsv">TSV</a>,
  <a href="$CGI_BASE_DIR/GetResultSet.cgi/$rs_set_name.xls?rs_set_name=$rs_set_name&format=excel">Excel</a>
  <BR><BR>
  ~;

  return $bottom_html;
}


###############################################################################
=head1 BUGS

Please send bug reports to SBEAMS-devel@lists.sourceforge.net

=head1 AUTHOR

Terry Farrah (terry.farrah@systemsbiology.org)

=head1 SEE ALSO

perl(1).

=cut
###############################################################################
1;

__END__
###############################################################################
###############################################################################
###############################################################################