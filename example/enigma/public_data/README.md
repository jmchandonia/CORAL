# Public data for the ENIGMA Data Clearinghouse

This directory contains some published data from the ENIGMA study:

Natural Bacterial Communities Serve as Quantitative Geochemical
Biosensors; Mark B. Smith, Andrea M. Rocha, Chris S. Smillie, Scott
W. Olesen, Charles Paradis, Liyou Wu, James H. Campbell, Julian
L. Fortney, Tonia L. Mehlhorn, Kenneth A. Lowe, Jennifer E. Earles,
Jana Phillips, Steve M. Techtmann, Dominique C. Joyner, Dwayne
A. Elias, Kathryn L. Bailey, Richard A. Hurt Jr., Sarah P. Preheim,
Matthew C. Sanders, Joy Yang, Marcella A. Mueller, Scott Brooks, David
B. Watson, Ping Zhang, Zhili He, Eric A. Dubinsky, Paul D. Adams, Adam
P. Arkin, Matthew W. Fields, Jizhong Zhou, Eric J. Alm, Terry
C. Hazen; mBio May 2015, 6 (3) e00326-15; DOI: 10.1128/mBio.00326-15

## Static datasets:

* locations_100ws.tsv = sampling locations (wells) from the 100 Well Survey

* samples_100ws.tsv = original samples from the 100 Well Survey

* samples_filter_100ws.tsv = filtered samples from the 100 Well Survey

* communities_filter_100ws.tsv = microbial communities from the filtered samples

* reads_kbase_100ws.tsv = references to 16S amplicon reads from the communities

* otus_zhou_100ws.tsv = OTUs called from the above reads

* taxa_zhou_100ws.tsv = Taxa used to annotate the above OTUs

## Dynamic datasets:

* generic_otu_count_zhou_100ws.json = a Brick containing OTU counts in each filtered sample

* generic_otu_id_zhou_100ws.json = a Brick containing taxonomic assignments for each OTU

* generic_field_data_adams.json = a Brick containing metals measurements for each sample

* generic_field_data_hazen.json = a Brick containing geochemical measurements and AODC counts for each sample

* generic_field_insitu_hach_hazen.json = a Brick containing in situ geochemical measurements for each sample

* generic_field_insitu_hazen.json = a Brick containing in situ geochemical measurements for each sample that were collected using a Hach Kit


## Process data:

* process_sampling_100ws.tsv = provenance of original sampling

* process_filter_100ws.tsv = provenance of filtering samples

* process_sequencing_100ws_16S.tsv = provenance of 16S amplicon sequencing

* process_otu_inference_zhou_100ws.tsv = provenance of OTU calling and classification

* process_environmental_measurements_adams.tsv = provenance of Adams Lab measurements

* process_environmental_measurements_hach_hazen.tsv = provenance of Hazen Lab Hach Kit measurements

* process_environmental_measurements_hazen.tsv = provenance of Hazen Lab in situ measurements

* process_environmental_measurements_2_hazen.tsv = provenance of Hazen Lab geochemistry and AODC measurements


## SETUP:

* all the above files should be copied to /home/coral/prod/data_import/data/ (or whatever directories you chose for "entity_dir", "process_dir", and "brick_dir" in config.json) before running your reload data notebook.


## Other Data Formats:

* The directory "bricks_nc_format" contains all of the above Bricks in NetCDF4 format.  The directory "bricks_tsv_format" contains all of the above Bricks in TSV format.  Both directories have instructions on how the files were made.
