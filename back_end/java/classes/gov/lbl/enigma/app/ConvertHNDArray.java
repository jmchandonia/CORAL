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

import static us.kbase.genericsutil.GenericsUtilCommon.*;

/**
   Convert HNDArray by removing first dimension, storing term
   in "dimension_variable_type" attribute.
*/
public class ConvertHNDArray {

    /**
       Check whether a HNDArray is DC format and heterogeneous
       */
    public static boolean isDCFormat(HNDArray hnda) throws Exception {
        // check whether HNDArray is really heterogenous
        if (!isHeterogeneous(hnda))
            return false;
            
        // get old data
        Long nd = hnda.getNDimensions();
        List<TypedValue> arrayContext = hnda.getArrayContext();
        if (arrayContext==null)
            return false;

        Term t = mapTerm("Data Variables Type");
        String dvtRef = t.getOtermRef();
        t = null;
        for (int i=0; i<arrayContext.size(); i++) {
            TypedValue tv = arrayContext.get(i);
            if (tv.getValueType().getOtermRef().equals(dvtRef)) {
                t = makeTerm(tv.getValue());
                break;
            }
        }
        return (t != null);
    }

    /**
       Convert HNDArray object to Data Clearinghouse format, by
       removing first dimension and storing term in
       "dimension_variable_type" attribute.
       */
    public static void toDCFormat(HNDArray hnda) throws Exception {       
        // check whether HNDArray is really heterogenous
        int numHet = hnda.getTypedValues().size();
        boolean isHeterogeneous = (numHet > 1);
        if (!isHeterogeneous)
            throw new Exception("can't convert HNDArray; is homogenous");
            
        // get old data
        Long nd = hnda.getNDimensions();
        if (nd<=1)
            throw new Exception("can't convert HNDArray; only one dimension");
        
        List<DimensionContext> dcs = hnda.getDimContext();
        DimensionContext dc = dcs.get(0);
        List<TypedValue> arrayContext = hnda.getArrayContext();
        if (arrayContext==null)
            arrayContext = new ArrayList<TypedValue>();
            
        // convert first dimension into context
        Term t = dc.getDataType();
        arrayContext.add(new TypedValue()
                         .withValueType(mapTerm("Data Variables Type"))
                         .withValue(makeValue(t.getTermName(),
                                              t.getOtermRef())));
        hnda.setArrayContext(arrayContext);
        
        // remove dimension
        dcs.remove(0);
        hnda.setDimContext(dcs);
        nd--;
        hnda.setNDimensions(nd);
    }

    /**
       Convert HNDArray object from Data Clearinghouse format to
       normal format, by changing "dimension_variable_type" back
       to the first dimension.
    */
    public static void fromDCFormat(HNDArray hnda) throws Exception {
        // check whether HNDArray is really heterogenous
        int numHet = hnda.getTypedValues().size();
        boolean isHeterogeneous = (numHet > 1);
        if (!isHeterogeneous)
            throw new Exception("can't convert HNDArray; is homogenous");
            
        // get old data
        Long nd = hnda.getNDimensions();
        List<DimensionContext> dcs = hnda.getDimContext();
        if (nd==null) {
            nd = new Long(dcs.size());
        }
        List<TypedValue> arrayContext = hnda.getArrayContext();
        if (arrayContext==null)
            throw new Exception("can't convert HNDArray; doesn't have any array context");

        Term t = mapTerm("Data Variables Type");
        String dvtRef = t.getOtermRef();
        t = null;
        for (int i=0; i<arrayContext.size(); i++) {
            TypedValue tv = arrayContext.get(i);
            if (tv.getValueType().getOtermRef().equals(dvtRef)) {
                t = makeTerm(tv.getValue());
                arrayContext.remove(i);
                break;
            }
        }
        if (t==null)
            throw new Exception("can't convert HNDArray; doesn't have 'data variables type' context");
        
            
        // convert "data variables type" back into dimension
        ArrayList<String> hetDataTypes = new ArrayList<String>();
        for (TypedValues tvs : hnda.getTypedValues())
            hetDataTypes.add(GenericsUtilCommon.toString(tvs,PRINT_BRIEF));
        
        DimensionContext dc = new DimensionContext()
            .withDataType(t)
            .withSize(new Long(numHet))
            .withTypedValues(Arrays.asList(new TypedValues()
                                           .withValueType(t)
                                           .withValues(new Values()
                                                       .withScalarType("string")
                                                       .withStringValues(hetDataTypes))));
        
        // add dimension and fix array context
        dcs.add(0,dc);
        hnda.setDimContext(dcs);
        nd++;
        hnda.setNDimensions(nd);
        hnda.setArrayContext(arrayContext);
    }

    // traverse jsonData, adding all to flattened array
    final public static void flattenArray(ArrayNode node, ArrayList flattened) {
        for (int i=0; i<node.size(); i++) {
            if (node.get(i) instanceof ArrayNode)
                flattenArray((ArrayNode)node.get(i), flattened);
            else
                flattened.add(node.get(i));
        }
    }

    final public static void flattenValues(ObjectNode jsonData) {
        for (JsonNode tv : jsonData.get("typed_values")) {
            ObjectNode values = (ObjectNode)tv.get("values");
            String scalarType = values.get("scalar_type").asText();
            String valuesType;
            if (scalarType.equals("object_ref"))
                valuesType = "object_refs";
            else if (scalarType.equals("oterm_ref"))
                valuesType = "oterm_refs";
            else
                valuesType = scalarType+"_values";

            ArrayNode valuesArray = (ArrayNode)values.get(valuesType);
            ArrayList newValues = new ArrayList();
            flattenArray(valuesArray, newValues);

            values.putArray(valuesType).addAll(newValues);
        }
    }
    
    final public static void main(String argv[]) {
        try {
            // load ontologies
            GenericsUtilCommon ont = new GenericsUtilCommon(Arrays.asList("/home/coral/prod/data_import/ontologies/enigma_specific_ontology.obo",
                                                                          "/home/coral/prod/data_import/ontologies/data_type_ontology.obo",
                                                                          "/home/coral/prod/data_import/ontologies/context_measurement_ontology.obo",
                                                                          "/home/coral/prod/data_import/ontologies/unit_standalone.obo"));

            // read from JSON
            ObjectMapper mapper = new ObjectMapper();
            File f = new File(argv[0]);
            ObjectNode jsonData = mapper.readValue(f,ObjectNode.class);

            // flatten any multidimensional typed values
            flattenValues(jsonData);

            // try to convert node to hnda
            HNDArray hnda = mapper.convertValue(jsonData, HNDArray.class);

            // convert to/from Data Clearinghouse format
            if ((argv.length > 1) && (argv[1].equals("-r")))
                fromDCFormat(hnda);
            else
                toDCFormat(hnda);

            // dump out data in JSON format:
            PrintfWriter outfile = new PrintfWriter(System.out);
            mapper.writeValue(outfile,hnda);
            outfile.close();
            
        }
        catch (Exception e) {
            System.out.println("Exception: "+e.getMessage());
            e.printStackTrace();
        }
    }
}
