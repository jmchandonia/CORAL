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

* wells_100ws.tsv = wells from the 100 Well Survey

* samples_100ws.tsv = original samples from the 100 Well Survey

* samples_filter_100ws.tsv = filtered samples from the 100 Well Survey

* communities_filter_100ws.tsv = microbial communities from the filtered samples

* reads_kbase_100ws.tsv = references to 16S amplicon reads from the communities

* otus_zhou_100ws.tsv = OTUs called from the above reads

* taxa_zhou_100ws.tsv = Taxa used to annotate the above OTUs

## Dynamic datasets:

* generic_otu_count_zhou_100ws.json = a Brick containing OTU counts in each filtered sample

* generic_otu_id_zhou_100ws.json = a Brick containing taxonomic assignments for each OTU

## Process data:

* process_sampling_100ws.tsv = provenance of original sampling

* process_filter_100ws.tsv = provenance of filtering samples

* process_sequencing_100ws_16S.tsv = provenance of 16S amplicon sequencing

* process_otu_inference_zhou_100ws.tsv = provenance of OTU calling and classification


