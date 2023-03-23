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
   Manipulate generic data for graphing
*/
public class FilterGeneric {
    final public static ObjectMapper mapper = new ObjectMapper()
        .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)
        .configure(SerializationFeature.FAIL_ON_EMPTY_BEANS, false);

    final public static void addToArray(ArrayNode a, Object o) throws Exception {
        if (o==null)
            a.add((String)null);
        else if (o instanceof String)
            a.add((String)o);
        else if (o instanceof Double)
            a.add((Double)o);
        else if (o instanceof Long)
            a.add((Long)o);
        else
            throw new Exception("unknown type "+o);
    }

    final public static void addNodes(ArrayNode arr, List<Values> list) throws Exception {
        for (Values v : list) {
            ArrayNode a = arr.addArray();
            for (Object o : GenericsUtilCommon.getObjects(v)) {
                if (o instanceof String)
                    a.add((String)o);
                else if (o instanceof Double)
                    a.add((Double)o);
                else if (o instanceof Long)
                    a.add((Long)o);
                else
                    throw new Exception("unknown type "+o);
            }
        }
        return;
    }

    final public static boolean isSameDimension(String var1, String var2) throws Exception {
        if ((var1==null) || (var2==null))
            return false;

        String dim1 = new String(var1);
        int pos = dim1.indexOf("/");
        if (pos > -1)
            dim1 = dim1.substring(0,pos);
        String dim2 = new String(var2);
        pos = dim2.indexOf("/");
        if (pos > -1)
            dim2 = dim2.substring(0,pos);
        if (dim1.equals(dim2))
            return true;
        else
            return false;
    }

    final public static void main(String argv[]) {
        try {
            // load ontologies
            GenericsUtilCommon ont = new GenericsUtilCommon(Arrays.asList("../data_import/ontologies/enigma_specific_ontology.obo",
                                                                          "../data_import/ontologies/data_type_ontology.obo",
                                                                          "../data_import/ontologies/context_measurement_ontology.obo",
                                                                          "../data_import/ontologies/unit_standalone.obo",
                                                                          "../data_import/ontologies/chebi.obo"));
            
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

            // load params from JSON
            ObjectNode params = (ObjectNode)mapper.readTree(argv[1]);
            // System.out.println(mapper.writerWithDefaultPrettyPrinter().writeValueAsString(params));
            
            // calculate all valid dimension ids.
            // if unique subindices in a dimension, then we can
            // fix subindices; otherwise, we must fix the whole dimension
            LinkedHashSet<String> allDimensionIDs = new LinkedHashSet<String>();
            List<DimensionContext> dcs = hnda.getDimContext();
            ArrayList<Long> dLengths = new ArrayList<Long>();
            ArrayList<Long> dLengthsHet = new ArrayList<Long>();
            for (int i=0; i<dcs.size(); i++) {
                DimensionContext dc = dcs.get(i);
                dLengths.add(new Long((long)dc.getSize()));
                if (i>0)
                    dLengthsHet.add(new Long((long)dc.getSize()));
                if (GenericsUtilCommon.hasPseudoDimensions(dc)) {
                    List<TypedValues> tvs = dc.getTypedValues();
                    for (int j=0; j<tvs.size(); j++) {
                        allDimensionIDs.add((i+1)+"/"+(j+1));
                        System.err.println((i+1)+"/"+(j+1)+": "+GenericsUtilCommon.toString(dc.getDataType(),PRINT_BRIEF)+", "+GenericsUtilCommon.toString(tvs.get(j).getValueType(),PRINT_BRIEF)+" "+dc.getSize());
                    }
                }
                else {
                    allDimensionIDs.add((i+1)+"");
                    System.err.println((i+1)+": "+GenericsUtilCommon.toString(dc.getDataType(),PRINT_BRIEF)+" "+dc.getSize());
                    List<TypedValues> tvs = dc.getTypedValues();
                    for (int j=0; j<tvs.size(); j++) {
                        // Values v = tvs.get(j).getValues();
                        // if (GenericsUtilCommon.hasUniqueValues(v)) {
                            allDimensionIDs.add((i+1)+"/"+(j+1));
                            System.err.println((i+1)+"/"+(j+1)+": "+GenericsUtilCommon.toString(dc.getDataType(),PRINT_BRIEF)+", "+GenericsUtilCommon.toString(tvs.get(j).getValueType(),PRINT_BRIEF)+" "+dc.getSize());
                            // }
                    }
                }
            }

            // make sure all dimension ids provided by user are valid
            // they don't have to all be variable or constant
            // check whether the user wants Z values, or different
            // data variable returned
            boolean needZ = false;
            if (params.has("z"))
                needZ = true;

            String dataVariable = null;
            if (params.has("data"))
                dataVariable = params.get("data").asText();
            
            List<String> variableDimensionIDs = new ArrayList<String>();
            for (JsonNode node : params.get("variable")) {
                variableDimensionIDs.add(node.asText());
            }
            Map<String,Long> constantDimensionIDMap = new HashMap<String,Long>();
            if (params.has("constant")) {
                for (Iterator<String> i = params.get("constant").fieldNames(); i.hasNext();) {
                    String dim = i.next();
                    Long value = params.get("constant").get(dim).asLong();
                    constantDimensionIDMap.put(dim,value);
                }
            }
            String pointLabels = null;
            if (params.has("point-labels"))
                pointLabels = params.get("point-labels").asText();

            Map<String,String> seriesFormats = new HashMap<String,String>();
            if (params.has("label-format")) {
                for (Iterator<String> i = params.get("label-format").fieldNames(); i.hasNext();) {
                    String dim = i.next();
                    String value = params.get("label-format").get(dim).asText();
                    seriesFormats.put(dim,value);
                }
            }
            
            Set<String> constantDimensionIDs = constantDimensionIDMap.keySet();
            Set<String> checkDimensionIDs = new HashSet<String>(constantDimensionIDs);
            checkDimensionIDs.addAll(variableDimensionIDs);
            if (pointLabels != null)
                checkDimensionIDs.add(pointLabels);
            for (String dimensionID : checkDimensionIDs) {
                if (!allDimensionIDs.contains(dimensionID)) {
                    boolean found = false;
                    String dim1 = new String(dimensionID);
                    int pos = dim1.indexOf("/");
                    if (pos > 0)
                        dim1 = dim1.substring(0,pos);
                
                    for (String dimensionID2 : allDimensionIDs) {
                        if (dimensionID2.startsWith(dim1+"/")) {
                            found = true;
                            continue;
                        }
                    }
                    if (!found)
                        throw new Exception("Dimension index "+dimensionID+" invalid for object");
                }
            }

            /*
              We used to keep track of all ids, to see if they're
              constant or variable.  However, this doesn't work without
              a calculation of whether the variables in a dimension
              are orthogonal

            // once all are known to be valid, remove them from the full set
            for (String dimensionID : checkDimensionIDs) {
                if (allDimensionIDs.contains(dimensionID))
                    allDimensionIDs.remove(dimensionID);
                else {
                    boolean found = false;
                    String dim1 = new String(dimensionID);
                    int pos = dim1.indexOf("/");
                    if (pos > 0)
                        dim1 = dim1.substring(0,pos);
                    for (Iterator<String> iterator = allDimensionIDs.iterator(); iterator.hasNext();) {
                        String dimensionID2 = iterator.next();
                        if (dimensionID2.startsWith(dim1+"/")) {
                            found = true;
                            iterator.remove();
                        }
                    }
                    if (!found)
                        throw new Exception("Dimension index "+dimensionID+" used in both constant and variable dimension");
                }
            }
            
            // Don't save any remaining dimensions as variable;
            // doing so requires a calculation of which dimensions
            // are orthogonal to which others
            // NO! variableDimensionIDs.addAll(allDimensionIDs);
            */

            System.err.println("Constant dimensions: "+constantDimensionIDMap.toString());
            System.err.println("Variable dimensions: "+variableDimensionIDs.toString());

            // must be at least 1 variable dimension
            // to return X and Y
            int nVariableDimensions = variableDimensionIDs.size();
            if (nVariableDimensions < 1)
                throw new Exception("There must be at least one variable dimension");
            if ((nVariableDimensions < 2) && needZ)
                throw new Exception("There must be at least two variable dimensions when returning Z values");

            // make the first variable dimension the X axis
            // and the second the Y axis (if returning Z values)
            String dimX = variableDimensionIDs.get(0);
            int nAxes = 1;
            String dimY = null;
            boolean sameXY = false; // are x/y same dimension?
            if (needZ) {
                dimY = variableDimensionIDs.get(1);
                nAxes = 2;
                // check if dimX and dimY are really same dimension
                sameXY = isSameDimension(dimX,dimY);

                // point labels need to be in the same dimension
                if (sameXY && (pointLabels != null)) {
                    if (!isSameDimension(dimX,pointLabels))
                        throw new Exception("point labels must be in the same dimension as X and Y variables");
                }

                // data variable needs to be in the same dimension
                if (sameXY && (dataVariable != null)) {
                    if (!isSameDimension(dimX,dataVariable))
                        throw new Exception("data variable must be in the same dimension as X and Y variables");
                }
            }

            // set up loop over all other variable dimensions
            ArrayList<String> seriesLabels = new ArrayList<String>();
            ArrayList<Values> valuesX = new ArrayList<Values>();
            ArrayList<Values> valuesY = new ArrayList<Values>();
            ArrayList<Values> valuesZ = null;
            if (needZ)
                valuesZ = new ArrayList<Values>();
            ArrayList<Values> valuesPointLabels = null;
            if (sameXY && (pointLabels != null))
                valuesPointLabels = new ArrayList<Values>();
            ArrayList<List> variableValues = new ArrayList<List>();
            ArrayList<String> variableNames = new ArrayList<String>();
            ArrayList<Long> curIndex = new ArrayList<Long>();
            int nSeries = 1;
            for (int i=nAxes; i<nVariableDimensions; i++) {
                TypedValues tv = GenericsUtilCommon.getTypedValues(hnda,variableDimensionIDs.get(i));
                Values v = tv.getValues();
                // lookup oterms if necessary
                if (v.getScalarType().equals("oterm_ref"))
                    GenericsUtilCommon.makeStringValues(v);
                if (variableDimensionIDs.get(i).indexOf("/") > 0)
                    v = GenericsUtilCommon.findUniqueValues(v);
                List objects = GenericsUtilCommon.getObjects(v);
                variableValues.add(objects);
                nSeries *= objects.size();
                String seriesFormat = seriesFormats.get(variableDimensionIDs.get(i));
                if (seriesFormat == null)
                    variableNames.add(GenericsUtilCommon.toString(tv,PRINT_BRIEF));
                else
                    variableNames.add(seriesFormat);
                curIndex.add(new Long(1L));
            }
            boolean hasSD = false; // do the y/z objects include SD?

            // loop over all variable dimensions
            for (int i=0; i<nSeries; i++) {
                // fix all constant and variable dimensions
                HashMap<String,Long> fixedDimensionMap = new LinkedHashMap<String,Long>();
                fixedDimensionMap.putAll(constantDimensionIDMap);
                String seriesLabel = "";
                for (int j=0; j<variableNames.size(); j++) {
                    if (j>0)
                        seriesLabel += "; ";
                    fixedDimensionMap.put(variableDimensionIDs.get(j+nAxes),
                                          curIndex.get(j));
                    // System.err.println("fdm: "+variableDimensionIDs.get(j+nAxes)+" = "+curIndex.get(j));
                    String variableName = variableNames.get(j);
                    int pos = variableName.indexOf("#VAR1");
                    if (pos == -1)
                        seriesLabel += variableName
                            + " = "
                            + variableValues.get(j).get((int)(curIndex.get(j).longValue())-1);
                    else // user-defined label format
                        seriesLabel += variableName.substring(0,pos)
                            + variableValues.get(j).get((int)(curIndex.get(j).longValue())-1)
                            + variableName.substring(pos+5,variableName.length());
                }
            
                // calculate the unique indices for each dimension
                ArrayList<HashSet<Long>> fixedIndices = new ArrayList<HashSet<Long>>();
                for (int j=0; j<dLengths.size(); j++) {
                    String dim1 = (j+1)+"";
                    if (fixedDimensionMap.get(dim1) != null) {
                        HashSet<Long> hsl = new HashSet<Long>();
                        hsl.add(fixedDimensionMap.get(dim1));
                        fixedIndices.add(hsl);
                    }
                    else {
                        // see if any subindices are fixed
                        DimensionContext dc = dcs.get(j);
                        boolean foundAny = false;
                        ArrayList<Long> valueIndices = new ArrayList<Long>();
                        List<TypedValues> tvs = dc.getTypedValues();
                        for (int k=0; k<tvs.size(); k++) {
                            String dimensionID = dim1 + "/" + (k+1);
                            Long l = fixedDimensionMap.get(dimensionID);
                            // System.err.println("looking for fdm "+dimensionID);
                            if (l==null) {
                                // System.err.println("not found");
                                valueIndices.add(null);
                            }
                            else {
                                // System.err.println("found");
                                valueIndices.add(l);
                                foundAny = true;
                            }
                        }
                        if (foundAny) {
                            // System.err.println("mui "+j);
                            fixedIndices.add(GenericsUtilCommon.mergeUniqueIndices(dc,
                                                                                   valueIndices));
                        }
                        else {
                            // System.err.println("null "+j);
                            fixedIndices.add(null);
                        }
                    }
                }
            
                // find the right set of values and fix them
                Long hetIndex = new Long(1L);
                ArrayList<Long> dLengthsFix = dLengths;
                if (GenericsUtilCommon.isHeterogeneous(hnda)) {
                    if (fixedIndices.get(0)==null)
                        throw new Exception("If getting data from heterogeneous matrix, the heterogeneous dimension can't be the X axis");
                    Iterator<Long> iter = fixedIndices.get(0).iterator();
                    if (iter==null)
                        throw new Exception("If getting data from heterogeneous matrix, the heterogeneous dimension can't be the X axis");
                    hetIndex = iter.next();
                    if (iter.hasNext())
                        throw new Exception("If getting data from heterogeneous matrix, the heterogeneous dimension can't be used in a series");
                    fixedIndices.remove(0);
                    dLengthsFix = dLengthsHet;
                }
                Values v = hnda.getTypedValues().get((int)(hetIndex.longValue())-1).getValues();
                int nValues = getObjects(v).size();
                int expectedNValues = 1;
                for (Long l : dLengthsFix)
                    expectedNValues *= l.intValue();
                System.err.println("expected "+expectedNValues+" values, found "+nValues);
                System.err.println("indices "+dLengthsFix.toString());
                System.err.println("fixing "+fixedIndices.toString());
                Values seriesFixedValues = GenericsUtilCommon.fixValues(v,
                                                                        dLengthsFix,
                                                                        fixedIndices);
                nValues = getObjects(seriesFixedValues).size();
                expectedNValues = 1;
                for (int j=0; j<dLengthsFix.size(); j++)
                    if (fixedIndices.get(j) == null)
                        expectedNValues *= dLengthsFix.get(j).intValue();
                    else
                        expectedNValues *= fixedIndices.get(j).size();
                if (expectedNValues != nValues)
                    throw new Exception("after fixing values, expected "+expectedNValues+" values, found "+nValues);
                System.err.println("result expected "+expectedNValues+" values, found "+nValues);

                // we need to average over all unfixed and
                // partially fixed dimensions
                // that are not dimX or dimY
                List<Long> dLengthsUnfixed = new ArrayList<Long>();
                List<Boolean> dimsToAvg = new ArrayList<Boolean>();
                for (int j=0; j<dLengthsFix.size(); j++)
                    if ((fixedIndices.get(j) == null) ||
                        (fixedIndices.get(j).size() > 1)) {
                        if (fixedIndices.get(j) ==  null)
                            dLengthsUnfixed.add(dLengthsFix.get(j));
                        else
                            dLengthsUnfixed.add(new Long(fixedIndices.get(j).size()));
                        String dim1 = (j+(GenericsUtilCommon.isHeterogeneous(hnda) ? 2 : 1))+"";
                        if (!(dim1.equals(dimX) ||
                              (dim1.equals(dimY)) ||
                              (dimX.startsWith(dim1+"/")) ||
                              ((dimY != null) && (dimY.startsWith(dim1+"/"))))) {
                            dimsToAvg.add(new Boolean(true));
                            hasSD = true;
                        }
                        else
                            dimsToAvg.add(new Boolean(false));
                    }

                Values averageSDFixedValues = null;
                if (hasSD) {
                    System.err.println("remaining dims "+dLengthsUnfixed.toString());
                    System.err.println("averaging "+dimsToAvg.toString());
                    averageSDFixedValues = GenericsUtilCommon.averageSDValues(seriesFixedValues,
                                                                              dLengthsUnfixed,
                                                                              dimsToAvg);

                    nValues = getObjects(averageSDFixedValues).size();
                    expectedNValues = 2;
                    for (int j=0; j<dLengthsUnfixed.size(); j++)
                        if (!dimsToAvg.get(j))
                            expectedNValues *= dLengthsUnfixed.get(j).intValue();
                    System.err.println("result expected "+expectedNValues+" values, found "+nValues);
                    if (expectedNValues != nValues)
                        throw new Exception("after averaging, expected "+expectedNValues+" values, found "+nValues);
                }
                else
                    averageSDFixedValues = seriesFixedValues;
                
                // get the X values
                Values seriesXValues = GenericsUtilCommon.getTypedValues(hnda,dimX).getValues();
                if (seriesXValues.getScalarType().equals("oterm_ref"))
                    GenericsUtilCommon.makeStringValues(seriesXValues);

                /*
                if (dimX.indexOf("/") > 0)
                    seriesXValues = GenericsUtilCommon.findUniqueValues(seriesXValues);
                else
                */
                    seriesXValues = GenericsUtilCommon.copyValues(seriesXValues);
                Values seriesYValues = null;
                Values seriesZValues = null;
                Values seriesPointLabels = null;
                if (needZ) {
                    // get Y in the same way as X
                    seriesYValues = GenericsUtilCommon.getTypedValues(hnda,dimY).getValues();
                    if (seriesYValues.getScalarType().equals("oterm_ref"))
                        GenericsUtilCommon.makeStringValues(seriesYValues);
                    
                /*
                    if (dimY.indexOf("/") > 0)
                        seriesYValues = GenericsUtilCommon.findUniqueValues(seriesYValues);
                    else
                */
                        seriesYValues = GenericsUtilCommon.copyValues(seriesYValues);
                    seriesZValues = averageSDFixedValues;

                    if (sameXY && (pointLabels != null)) {
                        seriesPointLabels = GenericsUtilCommon.getTypedValues(hnda,pointLabels).getValues();
                    }

                    if (sameXY && (dataVariable != null)) {
                        // should save time by not calculating
                        // seriesZValues in the first place
                        TypedValues tv = GenericsUtilCommon.getTypedValues(hnda,dataVariable);
                        seriesZValues = tv.getValues();
                    }
                }
                else
                    seriesYValues = averageSDFixedValues;

                // save the data for return to caller
                seriesLabels.add(seriesLabel);
                valuesX.add(seriesXValues);
                valuesY.add(seriesYValues);
                if (needZ)
                    valuesZ.add(seriesZValues);
                if (sameXY && (pointLabels != null))
                    valuesPointLabels.add(seriesPointLabels);
            
                // increment all indices
                if (i < nSeries-1) {
                    Long l = curIndex.get(0);
                    l++;
                    curIndex.set(0,l);
                    for (int j=0; j<variableNames.size()-1; j++) {
                        if (curIndex.get(j) > variableValues.get(j).size()) {
                            curIndex.set(j,new Long(1L));
                            l = curIndex.get(j+1);
                            l++;
                            curIndex.set(j+1,l);
                        }
                    }
                }
            }

            // return in plotly-like format
            ArrayNode rv = mapper.createArrayNode();
            if (needZ) {
                for (int i=0; i<nSeries; i++) {
                    ObjectNode seriesNode = rv.addObject();
                    seriesNode.put("label",seriesLabels.get(i));
                    ArrayNode x = seriesNode.putArray("x");
                    ArrayNode y = seriesNode.putArray("y");
                    ArrayNode z = seriesNode.putArray("z");
                    ArrayNode pl = null;
                    if (sameXY && (pointLabels != null))
                        pl = seriesNode.putArray("point-labels");
                    List<Object> xObjects = GenericsUtilCommon.getObjects(valuesX.get(i));
                    List<Object> yObjects = GenericsUtilCommon.getObjects(valuesY.get(i));
                    List<Object> zObjects = GenericsUtilCommon.getObjects(valuesZ.get(i));
                    List<Object> plObjects = null;
                    if (pl != null)
                        plObjects = GenericsUtilCommon.getObjects(valuesPointLabels.get(i));
                    int xLen = xObjects.size();
                    int yLen = yObjects.size();
                    if (sameXY && (xLen != yLen))
                        throw new Exception("Error - x and y are same dimension, different length");
                    for (int k=0; k<xLen; k++) {
                        Object ox = xObjects.get(k);
                        if (ox != null) {
                            if (sameXY) {
                                Object oy = yObjects.get(k);
                                if (oy != null) {
                                    addToArray(x,ox);
                                    addToArray(y,oy);
                                    int zIndex = k;
                                    if (hasSD)
                                        zIndex *= 2;
                                    Object oz = zObjects.get(zIndex);
                                    addToArray(z,oz);
                                    if (pl != null) {
                                        Object opl = plObjects.get(k);
                                        addToArray(pl,opl);
                                    }
                                }
                            }
                            else 
                                addToArray(x,ox);
                        }
                    }
                    if (!sameXY) {
                        for (int j=0; j<yLen; j++) {
                            Object o = yObjects.get(j);
                            if (o != null) {
                                addToArray(y,o);
                                ArrayNode zForY = z.addArray();
                                for (int k=0; k<xLen; k++) {
                                    o = xObjects.get(k);
                                    if (o != null) {
                                        // add Z value for j,k to zForY
                                        int zIndex = k*yLen + j;
                                        if (hasSD)
                                            zIndex *= 2;
                                        addToArray(zForY,zObjects.get(zIndex));
                                    }
                                }
                            }
                        }
                    }
                }
            }
            else {
                for (int i=0; i<nSeries; i++) {
                    ObjectNode seriesNode = rv.addObject();
                    seriesNode.put("label",seriesLabels.get(i));
                    ArrayNode x = seriesNode.putArray("x");
                    ArrayNode y = seriesNode.putArray("y");
                    ArrayNode sd = null;
                    if (hasSD)
                        sd = seriesNode.putArray("error_y");
                    List<Object> xObjects = GenericsUtilCommon.getObjects(valuesX.get(i));
                    List<Object> yObjects = GenericsUtilCommon.getObjects(valuesY.get(i));
                    int xLen = xObjects.size();
                    for (int j=0; j<xLen; j++) {
                        Object xo = xObjects.get(j);
                        if (xo != null) {
                            int yIndex = j;
                            if (hasSD)
                                yIndex *= 2;
                            Object yo = yObjects.get(yIndex);
                            if (yo != null) {
                                addToArray(x,xo);
                                addToArray(y,yo);
                                if (hasSD)
                                    addToArray(sd,yObjects.get(yIndex+1));
                            }
                        }
                    }
                }
            }
            
            System.out.println(mapper.writerWithDefaultPrettyPrinter().writeValueAsString(rv));
            
        }
        catch (Exception e) {
            System.out.println("Exception: "+e.getMessage());
            e.printStackTrace();
        }
    }
}
