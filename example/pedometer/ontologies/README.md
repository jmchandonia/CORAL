# Ontologies for the PEDOMETER Data Clearinghouse

This directory contains some sample ontologies customized for
use by PEDOMETER

Ontologies we defined:

* context_measurement_ontology = terms and microtypes to describe
  PEDOMETER data, probably useful for other environmental microbiology
  projects

* data_type_ontology = terms to describe high level data types in CORAL

* pedometer_specific_ontology = personnel and projects within PEDOMETER

* process_ontology = defined processes to create our static and dynamic objects

Other prerequisite ontologies:

* uo.obo = Units of measurement ontology (UO), [https://github.com/bio-ontology-research-group/unit-ontology/](https://github.com/bio-ontology-research-group/unit-ontology/).

* chebi.obo = Chemical Entities of Biological Interest, ChEBI [https://www.ebi.ac.uk/chebi/](https://www.ebi.ac.uk/chebi/)

* envo.obo = The Environment Ontology, [http://www.environmentontology.org/](http://www.environmentontology.org/)

## Installation

This is only required if you plan to edit these ontologies or want to know the provenance of how they were created or installed.

First, install ONTO-PERL, from [https://metacpan.org/pod/distribution/ONTO-PERL/ONTO-PERL.pod](https://metacpan.org/pod/distribution/ONTO-PERL/ONTO-PERL.pod)

```
apt-get install libexpat1-dev
perl -MCPAN -e shell
install EASR/ONTO-PERL/ONTO-PERL-1.45.tar.gz
install XML::Parser
```


### Obtain and set up external ontologies used by CORAL

** Units ontology:**

```
wget https://raw.githubusercontent.com/bio-ontology-research-group/unit-ontology/master/uo.obo
```

** ChEBI ontology:**

```
wget ftp://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.obo.gz
gzip -d chebi.obo.gz
```

** ENVO ontology:**

This is a particular version that I know works, since there are newer versions that won't load due to references to other ontologies not loaded in CORAL.

```
wget "https://github.com/EnvironmentOntology/envo/blob/v2019-03-14/envo.obo?raw=true" -O envo.obo
```

** NCBI Taxon ontology:**

```
wget http://ontologies.berkeleybop.org/ncbitaxon.obo
```


### Set up internal ontologies used by CORAL


**Set up data types ontology:**

_Edit to contain data types from your organization_

If starting from scratch:

```
./txt2ont.pl datatype DA data_type_ontology.txt > data_type_ontology.obo
```

Otherwise, make edits based on last version:

```
./txt2ont.pl datatype DA data_type_ontology.txt data_type_ontology.obo > data_type_ontology_new.obo
mv data_type_ontology_new.obo data_type_ontology.obo
```

**Set up context/measurement ontology:**

If starting from scratch:
```
./txt2ont.pl measure COMO context_measurement_ontology.txt > context_measurement_ontology.obo
```

Otherwise, make edits based on last version:
```
./txt2ont.pl measure COMO context_measurement_ontology.txt context_measurement_ontology.obo > context_measurement_ontology_new.obo
mv context_measurement_ontology_new.obo context_measurement_ontology.obo
```

**Set up PEDOMETER ontology:**

If starting from scratch:
```
./txt2ont.pl pedometer PEDOMETER pedometer_specific_ontology.txt > pedometer_specific_ontology.obo
```

Otherwise, make edits based on last version:
```
./txt2ont.pl pedometer PEDOMETER pedometer_specific_ontology.txt pedometer_specific_ontology.obo > pedometer_specific_ontology_new.obo
mv pedometer_specific_ontology_new.obo pedometer_specific_ontology.obo
```

**Set up process ontology:**

If starting from scratch:
```
./txt2ont.pl process PROCESS process_ontology.txt > process_ontology.obo
```

Otherwise, make edits based on last version:
```
./txt2ont.pl process PROCESS process_ontology.txt process_ontology.obo > process_ontology_new.obo
mv process_ontology_new.obo process_ontology.obo
```

## SETUP:

* all the obo files should be copied to /home/coral/prod/data_import/ontologies/ (or whatever directory you chose for "ontology_dir" in config.json) before running your reload data notebook.

* the larger ontologies (NCBI Taxon, ENVO, ChEBI) can take hours to load.  If you are re-running the reload data notebook and these are already loaded, add '"ignore": true' in /home/coral/prod/modules/var/upload_config.json next to those you don't want to reload.
