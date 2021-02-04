import { Injectable } from '@angular/core';
import {
  Brick,
  DataValue,
  BrickDimension,
  TypedProperty,
  DimensionVariable,
  Context,
  Term,
  MicroType
} from 'src/app/shared/models/brick';
import { isEqual } from 'lodash';

@Injectable({
  providedIn: 'root'
})
export class BrickFactoryService {

  public static createUploadInstance(template: any): Brick {
    const brick = new Brick();
    brick.template_type = template.text;
    brick.type = template.data_type as Term;
    brick.template_id = template.id;
    if (template.process) {
      brick.process = template.process as Term;
    }

    this.setTemplateDataValues(brick, template.data_vars);
    this.setTemplateDimensions(brick, template.dims);
    this.setTemplateProperties(brick, template.properties);

    return brick;
  }

  static setTemplateDataValues(brick: Brick, dataVars: any): void {
        // clear brickbuilder datavalues if different template is selected
        // this.brickBuilder.dataValues = [];

        dataVars.forEach((dataVar, idx) => {
          // set required to true in constructor
          const dataValue = new DataValue(idx, true);

          // set units to a term if its not empty or else null
          dataValue.units = (this.valuelessUnits(dataVar.units) ? null : dataVar.units) as Term;
          dataValue.typeTerm = dataVar.type;
          // dataValue.microType = dataVar.microtype;
          dataValue.scalarType = dataVar.scalar_type as Term;

          // create array of context objects for every data value that has context-
          if (dataVar.context && dataVar.context.length) {
            dataVar.context.forEach(ctx => {
              dataValue.context.push(this.setContext(ctx));
            });
          }

          // add dataValue to brick builder once values are set
          brick.dataValues.push(dataValue);
        });
  }

 static setTemplateDimensions(brick: Brick, dims: any[]) {

    // clear previous dimensions if new template is selected
    // this.brickBuilder.dimensions = [];

    dims.forEach((item, idx) => {
      // set required to true in constructor
      const dim = new BrickDimension(brick, idx, true);
      // set dimension type
      dim.type = new Term(item.type.id, item.type.text);
      
      // set dimension size
      dim.size = item.dim_vars.length;

      // create array of dimension variables from template
      item.dim_vars.forEach((dvItem, dvIdx) => {
        const dimVar = new DimensionVariable(dim, dvIdx, true);

        // set units to a term if units object does not contain empty values
        dimVar.units = (this.valuelessUnits(dvItem.units) ? null : dvItem.units) as Term;
        dimVar.typeTerm = dvItem.type;
        dimVar.scalarType = dvItem.scalar_type as Term;

        // create array of context objects for every dimension variable that has context
        if (dvItem.context && dvItem.context.length) {
          dvItem.context.forEach(ctx => {
            dimVar.context.push(this.setContext(ctx));
          });
        }
        // add variables to dimension once values are set
        dim.variables.push(dimVar);
      });
      // add dimension to brick once values are set
      brick.dimensions.push(dim);
    });
  }

  static setTemplateProperties(brick: Brick, props: any[]) {
        // clear previous properties if new template is selected
        // this.brickBuilder.properties = [];

        props.forEach((item, idx) => {
          // set required to true in constructor
          const prop = new TypedProperty(idx, true);

          // set units to a term if units object does not containe empty values
          prop.units = (this.valuelessUnits(item.units) ? null : item.units) as Term;
          prop.typeTerm = item.property as Term;
          prop.value = item.value as Term;
          prop.value = item.property.scalar_type === 'oterm_ref'
            ? prop.value as Term
            : prop.value.text;

          // create array of context objects for every property that has context
          if (item.context && item.context.length) {
            item.context.forEach(ctx => {
              prop.context.push(this.setContext(ctx));
             });
          }
          // add property to brick once values are set
          brick.properties.push(prop);
        });
  }

  static setContext(ctx): Context {
        // create new context from template
        const context = new Context();

        // set context properties
        context.required = ctx.required;
        context.typeTerm = ctx.property;
        context.value = new Term(ctx.value.id, ctx.value.text);
        if (!this.valuelessUnits(ctx.units)) {
          context.units = new Term(ctx.units.id, ctx.units.text);
        }
        return context;
  }

 static valuelessUnits(units) { return isEqual(units, {id: '', text: ''}); }

 public static createUploadInstanceFromLS(localStorageItem): Brick {
   const brick = new Brick();
   Object.entries(localStorageItem).forEach(([key, value]) => {
    //  brick[key] = value;
    switch(key) {
      case 'dataValues':
        brick[key] = this.createDataValuesFromLS(value);
        break;
      case 'dimensions':
        brick[key] = this.createDimensionsFromLS(value, brick);
        break;
      case 'properties':
        brick[key] = this.createPropertiesFromLS(value);
      default:
        brick[key] = value;
    }
   });
   return brick;
 }

static createDataValuesFromLS(LSDataValues): DataValue[] {
  return LSDataValues.map((LSDataValue, idx) => {
    const dataValue = new DataValue(idx, LSDataValue.required);
    Object.entries(LSDataValue).forEach(([key, value]) => {
      if (key === 'context') {
        dataValue.context = this.createContextFromLS(value);
      } else {
        dataValue[key] = value;
      }
    });
    return dataValue;
  });
}

static createDimensionsFromLS(LSDimensions, brick: Brick): BrickDimension[] {
  return LSDimensions.map((LSDimension, index) => {
    const dimension = new BrickDimension(brick, index, LSDimension.required);
    Object.entries(LSDimension).forEach(([key, value]) => {
      if (key === 'variables') {
        dimension.variables = this.createDimVarsFromLS(value, dimension);
      } else {
        dimension[key] = value;
      }
    });
    return dimension;
  });
}

static createDimVarsFromLS(LSDimVars, dimension: BrickDimension): DimensionVariable[] {
  return LSDimVars.map((LSDimVar, idx) => {
    const dimVar = new DimensionVariable(dimension, idx, LSDimVar.required);
    Object.entries(LSDimVar).forEach(([key, value]) => {
      if (key === 'context') {
        dimVar.context = this.createContextFromLS(value);
      } else {
        dimVar[key] = value;
      }
    });
    return dimVar;
  });
}

static createContextFromLS(LSContext): Context[] {
  return LSContext.map(LSContexton => {
    const context = new Context();
    Object.entries(LSContexton).forEach(([key, value]) => {
      context[key] = value;
    });
    return context;
  });
}

static createPropertiesFromLS(LSProperties): TypedProperty[] {
  return LSProperties.map((LSProperty, idx) => {
    const property: TypedProperty = new TypedProperty(idx, LSProperty.required, LSProperty.type, LSProperty.microType);
    Object.entries(LSProperty).forEach(([key, value]) => {
      if (key === 'context') {
        property.context = this.createContextFromLS(value);
      } else {
        property[key] = value;
      }
    });
    return property;
  });
}

}
