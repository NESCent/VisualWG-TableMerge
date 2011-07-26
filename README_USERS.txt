-----------------------------------------------------------------
          Spreadsheet merging for NESCent working group 
            Evolution of the Vertebrate Visual System
-----------------------------------------------------------------

Directory structure 
-------------------

incoming_submissions/  
   Inputs from the WG to NESCent. This directory is considered under
   control of the WG. Anything that NESCent programmers should take
   into account in the next merge will be more effective if placed
   here rather than in emails or folklore.

incoming_submissions/directives/
   Human-readable specifications and instructions, both for input
   spreadsheets and for the merge process. These are under control of
   the WG leaders.

incoming_submissions/data/
   Data spreadsheets. They should follow requirements from
   incoming_submissions/directives/.  Comma-separated (*.csv) files
   are much appreciated.
   
latest_results/
   Results of the most recent merge.  It is maintained to be a copy of
   the most recent past_details/yyyy-mm-dd/results.
 
past_details/
   Inputs, intermediate data, issue reports, and results of the past
   runs (including the most recent one.)  It contains subdirectories
   named yyyy-mm-dd-vn, with a date and, optionally, a version number.
   The yyyy-mm-dd date is when a snapshot of incoming_submissions/ was
   taken to run a merge.
   The vn version is used when the merge was re-run on the same
   yyyy-mm-dd data due to changes in the implementation or due to
   additional hand-made corrections of the input data, in either case
   affecting the results. 
   For more details on what in this directory, see a dedicated section
   below.

zArchive/ 
   Older activity within this WG, perhaps of historical interest. 
    

Workflow 
-------- 

New spreadsheets, or new versions of the spreadsheets are placed into
incoming_submissions/data/ on ongoing basis by their creators or by
someone on their behalf.  The spreadsheets are expected to conform to
instructions in incoming_submissions/directives/.  The submitters
should delete old spreadsheets that should not be used in future
merges.

From time-to-time, a snapshot of incoming_submissions/ is taken and a
merge is run on it.  Due to the possibility of manual work needed for
the merge, there can be a delay of several days before merge results
appear in past_details/yyyy-mm-dd and in latest_results/.

To leverage manual work needed to make submitted spreadsheets acceptable 
for merge, we wipe out the contents of incoming_submissions/data and 
replace them with the corrected spreadsheets from 
past_details/yyyy-mm-dd/data-used. The submitters are expected to use 
these spreadsheets as a starting point for subsequent submissions, or 
fix errors in their submissions themselves, as noted in 
past_details/yyyy-mm-dd/data-used/00PROVENANCE.txt (Note, however, that 
these notes only address fixes made for the last merge run.)

Submitters review issues pertaining to their reports, as documented in
past_details/yyyy-mm-dd/data-used/00PROVENANCE.txt and in the
appropriate directory under past_details/yyyy-mm-dd/reports.  They
re-submit corrected spreadsheets to incoming_submissions/data, to be
used in the next merge run.


Understanding past_details/yyyy-mm-dd-vn
----------------------------------------

data/ 
directives/ 
  The snapshot of the same-named directories under
  incoming_submissions/, taken on the date yyyy-mm-dd. These are kept
  for reference, in case there is a need to track problems in the
  results back to the inputs, while submissions to
  incoming_submissions/ may continue past yyyy-mm-dd.

data-used/
  
  The practice shown that files placed in incoming_submissions/data
  are not immediately suitable for automated merge processing due to
  trivial issues such as wrong format (proprietary Excel *.xls instead
  of the portable comma-separated *.csv) and header misspelling (e.g.,
  "Publication Genus" instead of "Pub. Genus"). We may correct such
  issues in the process of moving files from data/ to data-used/.  
  We try to mention all such corrections in the file
  data/00PROVENANCE.txt.  Submitters are advised to take these
  corrections into account in the next version of their data placed in
  incoming_submissions/data.

directives-used/ 

  This directory contains "meta-data" that is used programmatically to
  direct the merge process.  Currently, they consist of: 

  columns.csv - a table listing the headers of the input data
  spreadsheets and several parameters directing how the data under
  these headers should be processed.  This file is created by hand,
  based in the instructons in directives/, but is used
  programmatically by the merge process.

  taxa-resolver.tab - the taxonomic database that we use to resolve
  'published' binomials into 'canonical' binomials, plus their
  placement into Class, Order, and Family.
  
reports/ 

   Contains diagnostics about issues encountered during the merge
   process, which may need attention and correction in order to
   improve the quality of the merged data set at the next merge run.
   See a separate section below. 

results/ 

   The master spreadsheets resulting from the merge and a few reports
   about the megred data set.  See a separate section below.


Understanding reports/ 
----------------------

The directory contains files for issue reports pertaining to the whole
data set and individual directories pertaining to each submitted
spreadsheet.

Whole-dataset reports: 

taxaaction.tab: 

  A tab-separated table that lists actions taken by the taxa matching
  algorithm for the taxon in each row of each input spreadsheet. The
  report is sorted by submission, and the by original row order in the
  submission. 

Each subdirectory corresponding to a submisson spreadsheet contains: 

* issues.log: 
   A summary of a. column headings that are expected but missing;
   b. heading present but unexpected; and c. rows we ignored because
   the do not contain a species name.

* loadable.csv: 
   The comma-separated file used as input for the merge.  

* taxareport_all.csv: 
   A comma-separated file of all rows combined from
   taxareport_successes, taxareport_problems and taxareport_warnings

* taxareport_problems.csv: 
   A comma-separated file of all rows that failed (i.e. we could match
   the species name against our list). These may be due to spelling
   errors, or due to use of a synonym that we do not have in our list.

* taxareport_successes.csv: 
   A comma-separated file of all rows that matched against our species
   list and were incorporated into the merged spreadsheet

* taxareport_warnings.csv: 

   A comma-separated file of all rows where we matched the species
   name, but there was disagreement with the spreadsheet (the current
   binomial we found differed from the original, or at least one of
   class, order, family values differed). These rows were incorporated
   into the merged spreadsheet using the reference taxonomy.


Understanding results/ 
----------------------

  TODO


