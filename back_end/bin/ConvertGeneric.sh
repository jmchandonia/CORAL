#!/bin/bash

CLASSPATH=/home/coral/prod/java/classes:/home/coral/prod/java/GenericsUtil/lib/src:/home/coral/prod/java/jars/lib/jars/jackson/jackson-core-2.5.4.jar:/home/coral/prod/java/jars/lib/jars/jackson/jackson-annotations-2.5.4.jar:/home/coral/prod/java/jars/lib/jars/jackson/jackson-databind-2.5.4.jar:/home/coral/prod/java/jars/lib/jars/jackson/jackson-jaxrs-base-2.5.4.jar:/home/coral/prod/java/jars/lib/jars/jackson/jackson-jaxrs-json-provider-2.5.4.jar:/home/coral/prod/java/jars/lib/jars/jackson/jackson-module-jaxb-annotations-2.5.4.jar:/home/coral/prod/java/jars/lib/jars/opencsv/opencsv-3.9.jar:/home/coral/prod/java/jars/lib/jars/annotation/javax.annotation-api-1.3.2.jar:/home/coral/prod/java/jars/lib/jars/strbio/strbio-1.3.jar:/home/coral/prod/java/jars/lib/jars/apache_commons/commons-lang3-3.5.jar
export CLASSPATH

java -Xmx2000M gov.lbl.enigma.app.ConvertGeneric "$@"
