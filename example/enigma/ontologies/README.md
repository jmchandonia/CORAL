# Ontologies for the ENIGMA Data Clearinghouse

This directory contains some sample ontologies customized for
use by ENIGMA.

Ontologies we defined:

* context_measurement_ontology = terms and microtypes to describe
  ENIGMA data, probably useful for other environmental microbiology
  projects

* data_type_ontology = terms to describe high level data types in CORAL

* mixs = a list of MIxS environmental packages, turned into an ontology

* country = a list of countries from [http://www.insdc.org/country.html](http://www.insdc.org/country.html),
  turned into an ontology.  This should be replaced by a standard
  ontology of geopolitical locations, such as GAZ.

* continent = a list of continents, turned into an ontology.
  This should be replaced by a standard ontology of geopolitical
  locations, such as GAZ.

* enigma_specific_ontology = personnel and projects within ENIGMA

* process_ontology = defined processes to create our static and dynamic objects

Other prerequisite ontologies:

* unit_standalone.obo = Units of measurement ontology (UO), from the Phenotype and Trait Ontology (PATO), [https://github.com/bio-ontology-research-group/unit-ontology/](https://github.com/bio-ontology-research-group/unit-ontology/).  Standalone means references to PATO have been stripped out.

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
wget https://raw.githubusercontent.com/bio-ontology-research-group/unit-ontology/master/unit.obo
grep -v -e PATO -e "ontology: pato" unit.obo > unit_standalone.obo
```

** ChEBI ontology:**

```
wget ftp://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.obo.gz
gzip -d chebi.obo.gz
```

** ENVO ontology:**

This is a particular version that I know works, since there are newer versions that won't load due to references to other ontologies not loaded in CORAL.

```
wget "https://github.com/EnvironmentOntology/envo/blob/v2020-06-10/envo.obo?raw=true" -O envo.obo
```

** NCBI Taxon ontology:**

```
wget http://ontologies.berkeleybop.org/ncbitaxon.obo
```


### Set up internal ontologies used by CORAL


**Set up continents ontology:**
```
/bin/echo -e "Continent\n  Africa\n  Antarctica\n  Asia\n  Australia\n  Europe\n  North America\n  South America" > continent.txt
./txt2ont.pl continent CONTINENT continent.txt > continent.obo
```

**Set up countries ontology:**
```
wget http://insdc.org/country.html
lynx -dump -force_html country.html > country_raw.txt
```
_edit country_raw.txt to add indentation and hierarchy of terms, creating country.txt_

_finally, convert from txt to obo:_
```
./txt2ont.pl country COUNTRY country.txt > country.obo
```

**Set up MIxS ontology:**

_Edit mixs.txt to have list of MIxS packages, from [https://gensc.org/mixs/](https://gensc.org/mixs/)

_then convert from text to obo:_
```
./txt2ont.pl mixs MIxS mixs.txt > mixs.obo
```

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
./txt2ont.pl measure ME context_measurement_ontology.txt > context_measurement_ontology.obo
```

Otherwise, make edits based on last version:
```
./txt2ont.pl measure ME context_measurement_ontology.txt context_measurement_ontology.obo > context_measurement_ontology_new.obo
mv context_measurement_ontology_new.obo context_measurement_ontology.obo
```

**Set up ENIGMA ontology:**

If starting from scratch:
```
./txt2ont.pl enigma ENIGMA enigma_specific_ontology.txt > enigma_specific_ontology.obo
```

Otherwise, make edits based on last version:
```
./txt2ont.pl enigma ENIGMA enigma_specific_ontology.txt enigma_specific_ontology.obo > enigma_specific_ontology_new.obo
mv enigma_specific_ontology_new.obo enigma_specific_ontology.obo
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
