package gov.lbl.enigma.app;

import java.sql.*;
import java.io.*;
import java.util.*;
import java.text.*;
import org.strbio.io.*;
import org.strbio.math.*;
import org.strbio.mol.*;
import org.strbio.util.*;
import org.strbio.IO;
import us.kbase.kbasegenerics.*;
import us.kbase.genericsutil.GenericsUtilCommon;
import com.fasterxml.jackson.databind.*;
import com.fasterxml.jackson.databind.node.*;
import com.opencsv.*;

import static us.kbase.genericsutil.GenericsUtilCommon.*;

/**
   Convert Generic JSON to CSV, or CSV to JSON
*/
public class ConvertGeneric {
    final public static void main(String argv[]) {
        try {
            // load ontologies
            GenericsUtilCommon ont = new GenericsUtilCommon(Arrays.asList("/home/coral/prod/data_import/ontologies/enigma_specific_ontology.obo",
                                                                          "/home/coral/prod/data_import/ontologies/data_type_ontology.obo",
                                                                          "/home/coral/prod/data_import/ontologies/context_measurement_ontology.obo",
                                                                          "/home/coral/prod/data_import/ontologies/unit_standalone.obo",
                                                                          "/home/coral/prod/data_import/ontologies/chebi.obo"));
            
            ObjectMapper mapper = new ObjectMapper()
                .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)
                .configure(SerializationFeature.FAIL_ON_EMPTY_BEANS, false);
            if (argv[1].endsWith(".csv")) { // json to csv
                // read from JSON
                File f = new File(argv[0]);
                ObjectNode jsonData = mapper.readValue(f,ObjectNode.class);

                // flatten any multidimensional typed values
                ConvertHNDArray.flattenValues(jsonData);

                // try to convert node to hnda
                HNDArray hnda = mapper.convertValue(jsonData, HNDArray.class);

                // convert it from DC format if necessary
                if (ConvertHNDArray.isDCFormat(hnda))
                    ConvertHNDArray.fromDCFormat(hnda);
                
                CSVWriter outfile = new CSVWriter(new FileWriter(argv[1]));
                GenericsUtilCommon.writeCSV(hnda,
                                            GenericsUtilCommon.PRINT_OREF,
                                            outfile);
                outfile.close();
            }
            else if (argv[0].endsWith(".csv")) { // csv to json
                HNDArray hnda = GenericsUtilCommon.parseCSV(argv[0]);
                GenericsUtilCommon.mapPremapped(hnda);

                // convert to DC format if heterogeneous
                if (GenericsUtilCommon.isHeterogeneous(hnda))
                    ConvertHNDArray.toDCFormat(hnda);
                
                // dump out data in JSON format:
                PrintfWriter outfile = new PrintfWriter(argv[1]);
                mapper.writeValue(outfile,hnda);
                outfile.close();
            }
            else {
                throw new Exception("must convert from CSV to JSON, or JSON to CSV");
            }
        }
        catch (Exception e) {
            System.out.println("Exception: "+e.getMessage());
            e.printStackTrace();
        }
    }
}
