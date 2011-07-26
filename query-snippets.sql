-- Various query snippets

-- Nulls in the taxonomys table: 
select * 
from authority 
where synonym is null or species is null or genus is null or "family" is null 
   or "order" is null or "class" is null or sourceid is null
   
-- Look for potential homonyms: 
select synonym, count(*)
from authority
group by synonym
order by count(*) desc

-- Homonyms, with their multiple resolutions
with homonyms as (
 select synonym, count(*) as count
 from authority
 group by synonym
 having count(*) > 1
 order by count(*) desc
) 
select * 
from homonyms h join authority a
  on h.synonym = a.synonym
-- where a.sourceid not like 'COL:%'
order by h.count desc, h.synonym          


-- What classes are covered? 
select "class", count(*)
from taxonomy
group by "class"
order by count(*) desc


-- Genus+species from Taxonomy that do not resolve via a synonym.
-- Results (out of 119888 total): 
-- resolution:  not distinct   distinct
--   found      119129          58087
--   not found    1283          603 (most are "sp." or similar)
--   total      120412           58690
-- (total != found + not found  is due to homonyms (on synonym)
select (distinct) d.genus, d.species, '#', r.* 
from taxonomy d left join taxonomy r
  on r.synonym = d.genus || ' ' || d.species
where r.id is (not) null
;  

-- Synonyms that resolve the same according to more than one authority source. 
-- These may trigger a spurious ambiguity, if not dealed with
select synonym, genus, species, "family", "order", "class", count(*) as sources_count, array_agg(sourceid) as sources_ids
from authority
group by synonym, genus, species, "family", "order", "class" 
order by count(*) desc
-- 
--> 24 synonyms with count = 2 from the latest (March 2011) table from Peter


--------------------------------------------------------------------

-- A view to see just the submitted names, no data 
create view submnames as 
select id, "Submission", 
       "Name used in publication genus", "Name used in publication species", 
       "Class", "Order", "Family", "Genus", "Species", "Subspecies", 
       "ITIS number", "Reference"
from upload

select * from submnames


create view submnames as 
select id,
Submission varchar,
  Linenum varchar,
  ITIS number varchar,
  Name used in publication genus varchar,
  Name used in publication species varchar,
  Common name varchar,
  Class varchar,
  Order varchar,
  Family varchar,
  Genus varchar,
  Species varchar,
  Subspecies varchar
 from upload;



create view taxamatch as 
select d.*, r.*  
from submnames d left join authority r
     on d."Name used in publication genus" || ' ' || d."Name used in publication species" = r.synonym
order by d.upload_id



['upload_id', 'Submission', 'Linenum', 'ITIS number', 'Name used in publication genus', 'Name used in publication species', 'Common name', 'Class', 'Order', 'Family', 'Genus', 'Species', 'Subspecies', 'authority_id', 'synonym', 'genus', 'species', 'family', 'order', 'class', 'sourceid']
(1, 'subm1', '2', None, 'Absenticus', 'absentus', None, 'Submclass', 'Submorder', 'Submfam', 'Absenticus', 'absentus', None, None, None, None, None, None, None, None, None)
(2, 'subm1', '3', None, 'Exactus', 'agreeus', None, 'Exclass', 'Exorder', 'Exfamily', 'Exacto', 'agreeico', None, 2, 'Exactus agreeus', 'Exacto', 'agreeico', 'Exfamily', 'Exorder', 'Exclass', 'test:0001')
(3, 'subm1', '4', None, 'Exactus', 'disagreeus', None, 'Exclass', 'Exorder', 'Exfamily', 'Exacto', 'disagreeico', None, 3, 'Exactus disagreeus', 'Auexacto', 'authorico', 'Aufamily', 'Auorder', 'Auclass', 'test:0002')
(4, 'subm2', '2', None, 'Ambigus', 'fammatchus', None, 'Authclass', 'Authorder', 'Fammatchea', 'Ambigo', 'fammatcho', None, 6, 'Ambigus fammatchus', 'Ambigo2', 'famnomatcho2', 'Famnomatchea2', 'Authorder2', 'Authclass', 'test:0005')
(4, 'subm2', '2', None, 'Ambigus', 'fammatchus', None, 'Authclass', 'Authorder', 'Fammatchea', 'Ambigo', 'fammatcho', None, 5, 'Ambigus fammatchus', 'Ambigo1', 'famnomatcho1', 'Famnomatchea1', 'Authorder1', 'Authclass', 'test:0004')
(4, 'subm2', '2', None, 'Ambigus', 'fammatchus', None, 'Authclass', 'Authorder', 'Fammatchea', 'Ambigo', 'fammatcho', None, 4, 'Ambigus fammatchus', 'Ambigo', 'fammatcho', 'Fammatchea', 'Authorder', 'Authclass', 'test:0003')
(5, 'subm2', '3', None, 'Ambigus', 'fammatchus disagrus', None, 'Submclass', 'Submorder', 'Famagrea', 'Subambigo', 'disagrus', None, 8, 'Ambigus fammatchus disagrus', 'Ambigus', 'disargus', 'Famdisagrea', 'Auorder', 'Auclass', 'test:0007')
(5, 'subm2', '3', None, 'Ambigus', 'fammatchus disagrus', None, 'Submclass', 'Submorder', 'Famagrea', 'Subambigo', 'disagrus', None, 7, 'Ambigus fammatchus disagrus', 'Ambigus', 'disargus', 'Famagrea', 'Auorder', 'Auclass', 'test:0006')
(6, 'subm2', '4', None, 'Ambigus', 'nofamus', None, 'Nofclass', 'Noforder', 'Submfamea', 'Ambigus', 'nofamus', None, 11, 'Ambigus nofamus', 'Ambigus3', 'nofamus3', 'Aufamily3', 'Auorder3', 'Auclass3', 'test:0010')
(6, 'subm2', '4', None, 'Ambigus', 'nofamus', None, 'Nofclass', 'Noforder', 'Submfamea', 'Ambigus', 'nofamus', None, 10, 'Ambigus nofamus', 'Ambigus2', 'nofamus2', 'Aufamily2', 'Auorder2', 'Auclass2', 'test:0009')
(6, 'subm2', '4', None, 'Ambigus', 'nofamus', None, 'Nofclass', 'Noforder', 'Submfamea', 'Ambigus', 'nofamus', None, 9, 'Ambigus nofamus', 'Ambigus1', 'nofamus1', 'Aufamily1', 'Auorder1', 'Auclass1', 'test:0008')
(7, 'subm2', '5', None, 'Ambigus', 'fambigus', None, 'Submclass', 'Submorder', 'Aufamea', 'Ambigus', 'fambigus', None, 13, 'Ambigus fambigus', 'Ambigus2', 'fambigus2', 'Aufamea', 'Auorder2', 'Auclass', 'test:0012')
(7, 'subm2', '5', None, 'Ambigus', 'fambigus', None, 'Submclass', 'Submorder', 'Aufamea', 'Ambigus', 'fambigus', None, 12, 'Ambigus fambigus', 'Ambigus1', 'fambigus1', 'Aufamea', 'Auorder1', 'Auclass', 'test:0011')
(8, 'subm3', '2', None, 'Absenticus', 'absentus', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
(9, 'subm3', '3', None, 'Exactus', 'agreeus', None, None, None, None, None, None, None, 2, 'Exactus agreeus', 'Exacto', 'agreeico', 'Exfamily', 'Exorder', 'Exclass', 'test:0001')
(10, 'subm3', '4', None, 'Exactus', 'disagreeus', None, None, None, None, None, None, None, 3, 'Exactus disagreeus', 'Auexacto', 'authorico', 'Aufamily', 'Auorder', 'Auclass', 'test:0002')
(11, 'subm3', '5', None, 'Ambigus', 'fammatchus', None, None, None, None, None, None, None, 6, 'Ambigus fammatchus', 'Ambigo2', 'famnomatcho2', 'Famnomatchea2', 'Authorder2', 'Authclass', 'test:0005')
(11, 'subm3', '5', None, 'Ambigus', 'fammatchus', None, None, None, None, None, None, None, 5, 'Ambigus fammatchus', 'Ambigo1', 'famnomatcho1', 'Famnomatchea1', 'Authorder1', 'Authclass', 'test:0004')
(11, 'subm3', '5', None, 'Ambigus', 'fammatchus', None, None, None, None, None, None, None, 4, 'Ambigus fammatchus', 'Ambigo', 'fammatcho', 'Fammatchea', 'Authorder', 'Authclass', 'test:0003')
(12, 'subm3', '6', None, 'Ambigus', 'fammatchus disagrus', None, None, None, None, None, None, None, 8, 'Ambigus fammatchus disagrus', 'Ambigus', 'disargus', 'Famdisagrea', 'Auorder', 'Auclass', 'test:0007')
(12, 'subm3', '6', None, 'Ambigus', 'fammatchus disagrus', None, None, None, None, None, None, None, 7, 'Ambigus fammatchus disagrus', 'Ambigus', 'disargus', 'Famagrea', 'Auorder', 'Auclass', 'test:0006')
(13, 'subm3', '7', None, 'Ambigus', 'nofamus', None, None, None, None, None, None, None, 11, 'Ambigus nofamus', 'Ambigus3', 'nofamus3', 'Aufamily3', 'Auorder3', 'Auclass3', 'test:0010')
(13, 'subm3', '7', None, 'Ambigus', 'nofamus', None, None, None, None, None, None, None, 10, 'Ambigus nofamus', 'Ambigus2', 'nofamus2', 'Aufamily2', 'Auorder2', 'Auclass2', 'test:0009')
(13, 'subm3', '7', None, 'Ambigus', 'nofamus', None, None, None, None, None, None, None, 9, 'Ambigus nofamus', 'Ambigus1', 'nofamus1', 'Aufamily1', 'Auorder1', 'Auclass1', 'test:0008')
(14, 'subm3', '8', None, 'Ambigus', 'fambigus', None, None, None, None, None, None, None, 13, 'Ambigus fambigus', 'Ambigus2', 'fambigus2', 'Aufamea', 'Auorder2', 'Auclass', 'test:0012')
(14, 'subm3', '8', None, 'Ambigus', 'fambigus', None, None, None, None, None, None, None, 12, 'Ambigus fambigus', 'Ambigus1', 'fambigus1', 'Aufamea', 'Auorder1', 'Auclass', 'test:0011')




--- Taxa match reporting 
select "Linenum", "Name used in publication genus" , "Name used in publication species", 
       "Class", "Order", "Family", "Genus", "Species", "Subspecies", 
       "taxon_action", "data_action", 
       (case when auth_used = authority_id then '*' end) as auth_used, 
       "authority_id", "synonym", "class", "order", "family", "genus", "species", "sourceid"
from taxaaction
where "Submission" = 'subm3' 
--  and "taxon_action" in ('override', 'foundmany', 'notfound')
    and true
order by "upload_id"


---- Creation of masterraw
with resolved_taxa as (
  select "upload_id",
         "Submission", "Linenum", "Name used in publication genus" , "Name used in publication species", 
         "sourceid", "class", "order", "family", "genus", "species"
  from taxaaction
  where auth_used = authority_id
)
select resolved_taxa.*,  
       "Summary", "Reference", 
       "Body mass", "Body length" 
into masterraw
from resolved_taxa join upload
  on resolved_taxa.upload_id = upload.upload_id 
;


select * from masterraw  
order by "class", "order", "family", "genus", "species"


-----------------------------------------------------------------------------------------------
    Overview statistics 
-----------------------------------------------------------------------------------------------
(outputs are for Tue Match 15 data )

-- Total rows submitted 
select count(*) from upload
--- 46108


-- Status counts for the submitted lines 
with linestatus as (
  select distinct upload_id, fam_match, taxon_action, data_action
  from taxaaction
)
select taxon_action, data_action, count(*)
from linestatus
group by taxon_action, data_action
order by data_action, taxon_action

-- taxon_action	data_action	count
-- "override"; 	"accept";	23394
-- "writein";	"accept";	2
-- "ok";	"accept";	12628
-- "foundmany";	"ignore";	43
-- "notfound";	"ignore";	10041


-- Line status counts with breakdown for submissions
with linestatus as (
  select distinct upload_id, "Submission", fam_match, taxon_action, data_action
  from taxaaction
)
select "Submission", taxon_action, data_action, count(*)
from linestatus
group by "Submission", taxon_action, data_action
order by "Submission", data_action, taxon_action


-- Number of rows per species in masterraw
select  "class", "order", "family", "genus", "species", count(*)
from masterraw
group by "class", "order", "family", "genus", "species"
order by count(*) desc 

-- Histogram: Number of species that have a particular number of data rows
with rows_per_species as (
  select  "class", "order", "family", "genus", "species", count(*) as rowcount
  from masterraw
  group by "class", "order", "family", "genus", "species"
  order by count(*) desc 
)
select rowcount as "rows per species", count(*) as "number such species"
from rows_per_species
group by rowcount 
order by rowcount asc

-- "rows per species"	"number such species"
-- 1;			1183
-- 2;			549
-- 3;			3282
-- 4;			1077
-- 5;			746
-- .......
-- 90			1


--- Data density summaries 
--- 
with data_point_counts as (
  select  "class", "order", "family", "genus", "species", 
          count(*) as "rowcount", 
          count("Body mass") as "Body mass", count("Standard length") as "Standard length"
          -- add more traits here
  from masterraw
  group by "class", "order", "family", "genus", "species"
  order by count(*) desc 
),
data_point_presence as (
  select  "class", "order", "family", "genus", "species", 
          (case when "Body mass" > 0 then 1 else 0 end) as "Body mass", 
          (case when "Standard length" > 0 then 1 else 0 end) as "Standard length"
  from data_point_counts
),
trait_counts_by_class as (
  select "class", count("order" || ' '|| "family" || ' ' || "genus" || ' '|| "species"), 
         sum("Body mass") as "Body mass", sum("Standard length") as "Standard length"
         -- more traits here
  from data_point_presence
  group by "class"
)
select * 
from trait_counts_by_class


-- real arith does not work here... 
trait_percentage_by_class as (
  select "class", "species count",
         ((cast ("Body mass" as real)) /  cast ("species count" as real)) as "Body mass"
         -- more traits here
  from trait_counts_by_class 


------------------------------------------------------------------------------------------------------

--  Full taxon match report for Olaf 

select 
	 a."upload_id", a."Submission", a."Linenum", 
	 a."Name used in publication genus" , a."Name used in publication species", a."Common name", 
         u."Reference", u."Original reference of the data point", 
         u."Class", u."Order", u."Family", u."Genus", u."Species", u."Subspecies", 
         u."ITIS number",
         a."pub_match", a."fam_match", a."curr_agreement", a."taxon_action", a."data_action", 
         (case when a."auth_used" = a."authority_id" then '*' end) as "auth_used", 
         a."synonym", a."class", a."order", a."family", a."genus", a."species", a."sourceid"
from taxaaction a join upload u
     on a.upload_id = u.upload_id  
order by a."upload_id"

order by a."Name used in publication genus" , a."Name used in publication species", a."data_action", a."taxon_action" 


------------------------------------------------------------------------------------------------------
--     Data quality:  Summary and Reference columns
------------------------------------------------------------------------------------------------------


-- Who uses the "Summary" column: 
select "Submission", "Summary", count(*)
from masterraw
where "Summary" is not null and "Summary" <> 'NO'
group by "Submission", "Summary"
order by "Submission", "Summary"
-- 
-- "Kara Yopak 00_key_ai";"YES";561
-- "Meg Hall Morphology March 2011";"Yes";1473
-- "Meg Hall Morphology March 2011";"yes";661
-- "Moritz_Dominy";"Yes";13


-- Lines with Summary = yes 
select "Submission", "Linenum", "genus", "species", "Summary", "Reference", "Original reference of the data point", "Notes",  
       "Body mass",  "Tapeta",  "Fovea",  "Number of area centralis",  "Vertical streak",  "Horizontal streak",  "Inflected streak",  "Radial anisotropy",  "Central retinal specialization",  "Dorsal retinal specialization",  "Dorsotemporal retinal specialization",  "Temporal retinal specialization",  "Ventrotemporal retinal specialization",  "Ventral retinal specialization",  "Ventronasal retinal specialization",  "Nasal retinal specialization",  "Dorsonasal retinal specialization",  "Peak Retinal Ganglion Cell Density",  "Total # of retinal ganglion cells",  "Brain volume",  "Brain mass",  "Mesencephalon",  "Optic tectum",  "Superior colliculus",  "Dominant photoreceptor type",  "Photoreceptor layer thickness",  "Mean rod diameter",  "Mean cone diameter",  "Eye axial diameter",  "Eye transverse diameter",  "Corneal area",  "Derived focal length",  "Pupil shape (round in any light condition)",  "Eye placement in head",  "Visual sexual dimorphism",  "Body size dimorphism",  "Morphological dimorphism",  "Light levels",  "Nocturnal",  "Diurnal",  "Crepuscular",  "Aquatic",  "Amphibious",  "Fossorial",  "Cursorial",  "Arboreal",  "Aerial",  "Mobility of fastest food item",  "Diet",  "Visual habitat complexity"
from masterraw 
where  lower("Summary") = 'yes'
order by "Submission", "Linenum"


-- Whether people make use of the "Reference" columns
select  "Submission", "Reference", "Original reference of the data point", count(*)
from masterraw
group by "Submission", "Reference", "Original reference of the data point"
order by "Submission", "Reference", "Original reference of the data point"


-- Who makes use of "Original reference of the data point" and how:
select "Submission", "Reference", "Original reference of the data point", count(*)
from masterraw
where "Original reference of the data point" is not null
group by "Submission", "Reference", "Original reference of the data point"
order by "Submission", "Reference", "Original reference of the data point"

-- "Tom Lisney 20Mar2011": mostly duplicates info from Reference, but there are a few cases when they are different
-- "Kara Yopak behavioral_3-18-11": when Orig Ref is not null, it has value different from Reference
-- "Kara Yopak 00_key_ai": apparently, Orig Ref is used instead of Reference: Reference is always null


------------------------------------------------------------------------------------------------------
--     Summarizing the data points  
------------------------------------------------------------------------------------------------------


------------------------------------------------------------------------------------------------------
--     2011-06-24    
------------------------------------------------------------------------------------------------------

-- Report for "not found" taxa

with array_summary as (
select "Pub. Genus", "Pub. Species", "Pub. Subspecies", count(*) as num_data_rows, 
       array_agg(distinct (coalesce("Pub. Class", 'BLANK') || ' ' || 
                                           coalesce("Pub. Order", 'BLANK') || ' ' || 
                                           coalesce("Pub. Family", 'BLANK'))) as COF_arr, 
       array_agg(distinct "Submission") as subm_arr
from taxaaction
where taxon_action = 'notfound'
group by "Pub. Genus", "Pub. Species", "Pub. Subspecies"
)
select "Pub. Genus", "Pub. Species", "Pub. Subspecies", num_data_rows, 
       array_to_string(COF_arr , E'\r\n') as "Pub Class-Order-Family", 
       array_length(COF_arr, 1) as "num_COF",
       array_to_string(subm_arr, E'\r\n') as submissions, 
       array_length(subm_arr, 1) as num_submissions
from array_summary
order by num_data_rows desc
--order by num_submissions desc


-- All taxonomy resolution issues (errors and warnings) in one report
-- 
with 
actsets as (
select "Pub. Genus", "Pub. Species", "Pub. Subspecies", 
       "Pub. Genus" || ' ' || "Pub. Species" || ' ' || coalesce("Pub. Subspecies", 'BLANK') as trinomial, 
       count(*) as num_data_rows, 
       count (distinct taxon_action) as txact_count, array_agg(distinct taxon_action) as txacts,
       array_agg(distinct (coalesce("Pub. Class", 'BLANK') || ' ' || 
                           coalesce("Pub. Order", 'BLANK') || ' ' || 
                           coalesce("Pub. Family", 'BLANK'))) as COF_arr, 
       array_agg(distinct "Submission") as subm_arr 
from taxaaction 
where taxon_action is not null   --this ensures that num_data_rows is what is says
group by "Pub. Genus", "Pub. Species", "Pub. Subspecies"
), 
authtaxa as (
select 
      "Pub. Genus" || ' ' || "Pub. Species" || ' ' || coalesce("Pub. Subspecies", 'BLANK') as trinomial, 
       array_agg(distinct coalesce("genus", '') || ' ' || 
                          coalesce("species", '') || ' - ' ||
                          coalesce("class", '') || ' ' || 
                          coalesce("order", '') || ' ' || 
                          coalesce("family", '') || ' - ' ||
                          coalesce("sourceid", '') 
                          ) as auth_taxa_corr
from taxaaction
group by "Pub. Genus", "Pub. Species", "Pub. Subspecies"
)
select "Pub. Genus", "Pub. Species", "Pub. Subspecies", 
       num_data_rows, 
       array_to_string(COF_arr , E';\r\n') as "Pub. Class Order Family", 
       array_to_string(subm_arr, E';\r\n') as submissions, 
       array_to_string(txacts, '; ') as "Match result",  
       array_to_string(auth_taxa_corr, E';\r\n') as "Authoritative Taxon(s)", 
       '#' as "#",
       ' ' as "WG Genus", ' ' as "WG Species", ' ' as "WG Class", ' ' as "WG Order", ' ' as "WG Family", 
       ' ' as "WG comment" 
from actsets join authtaxa using (trinomial)
where ARRAY['override' :: varchar, 'notfound' :: varchar, 'foundmany' :: varchar] && txacts
order by num_data_rows desc 


------------------------------------------------------------------------------------------------------
--     2011-06-28
------------------------------------------------------------------------------------------------------

--  Extract authority sources from source ids 
--
select distinct substring(sourceid from '^.+:')
from authority
--
select substring(sourceid from '^.+:') as auth, count(*)
from authority
group by auth
--> 
"ATO:";6752
"CASSPC:";11302
"COL:";86964
"FISHBASE:";14128
"IOC:";10384
"NCBITaxon:";13759
"TAO:";1
"TTO:";32610
"TTOCurator:";1
"doi:";1
"http:";745


-- Details for the "doi" and "http" sourceids
select distinct sourceid 
from authority 
where sourceid like 'doi:%'
   or sourceid like 'http:%'
--
select sourceid, count(*) 
from authority 
where sourceid like 'doi:%'
   or sourceid like 'http:%'
group by sourceid
--> 
"doi:10.1002/jmor.10447";1
"http://www.iucnredlist.org/initiatives/amphibians";703
"http://www.itis.gov/";42

