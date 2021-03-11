#!/bin/bash

# CLASSPATH=/home/coral/prod/java/classes:/home/coral/prod/java/GenericsUtil/lib/src:/home/coral/prod/java/jars/lib/jars/jackson/jackson-core-2.5.4.jar:/home/coral/prod/java/jars/lib/jars/jackson/jackson-annotations-2.5.4.jar:/home/coral/prod/java/jars/lib/jars/jackson/jackson-databind-2.5.4.jar:/home/coral/prod/java/jars/lib/jars/jackson/jackson-jaxrs-base-2.5.4.jar:/home/coral/prod/java/jars/lib/jars/jackson/jackson-jaxrs-json-provider-2.5.4.jar:/home/coral/prod/java/jars/lib/jars/jackson/jackson-module-jaxb-annotations-2.5.4.jar:/home/coral/prod/java/jars/lib/jars/opencsv/opencsv-3.9.jar:/home/coral/prod/java/jars/lib/jars/annotation/javax.annotation-api-1.3.2.jar:/home/coral/prod/java/jars/lib/jars/strbio/strbio-1.3.jar
# export CLASSPATH

# javac /home/coral/prod/java/classes/gov/lbl/enigma/app/*.java

PROJECT_ROOT="$(grep -o '"project_root": "[^"]*' ../back_end/python/var/config.json | grep -o '[^"]*$')"

CLASSPATH="${PROJECT_ROOT}/java/classes:${PROJECT_ROOT}/java/GenericsUtil/lib/src:${PROJECT_ROOT}/java/jars/lib/jars/jackson/jackson-core-2.5.4.jar:${PROJECT_ROOT}/java/jars/lib/jars/jackson/jackson-annotations-2.5.4.jar:${PROJECT_ROOT}/java/jars/lib/jars/jackson/jackson-databind-2.5.4.jar:${PROJECT_ROOT}/java/jars/lib/jars/jackson/jackson-jaxrs-base-2.5.4.jar:${PROJECT_ROOT}/java/jars/lib/jars/jackson/jackson-jaxrs-json-provider-2.5.4.jar:${PROJECT_ROOT}/java/jars/lib/jars/jackson/jackson-module-jaxb-annotations-2.5.4.jar:${PROJECT_ROOT}/java/jars/lib/jars/opencsv/opencsv-3.9.jar:${PROJECT_ROOT}/java/jars/lib/jars/annotation/javax.annotation-api-1.3.2.jar:${PROJECT_ROOT}/java/jars/lib/jars/strbio/strbio-1.3.jar"
export CLASSPATH

javac "$PROJECT_ROOT"/java/classes/gov/lbl/enigma/app/*.java
