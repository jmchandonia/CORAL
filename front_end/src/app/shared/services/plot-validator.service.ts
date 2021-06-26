import { Injectable } from '@angular/core';
import { PlotlyBuilder, Constraint, ConstraintVariable, AxisOption, Axis } from 'src/app/shared/models/plotly-builder';
import { ObjectMetadata } from '../models/object-metadata';
import { PlotlyConfig } from '../models/plotly-config';

@Injectable({
  providedIn: 'root'
})
export class PlotValidatorService {

  constructor() { }

  public static validPlot(plot: PlotlyBuilder): boolean {
    if (!plot.plot_type) return false;

    for(const [_, val] of Object.entries(plot.axes)) {
      if (!val.data) return false;
    }

    for (const constraint of plot.constraints) {
      if (!this.validConstraint(constraint)) return false;
    }

    return true;
  }

  static validConstraint(constraint: Constraint): boolean {
    if (constraint.constrain_by_mean) return true;
    for (const variable of constraint.variables) {
      if (!this.validConstraintVariable(variable)) return false;
    }
    return true;
  }

  static validConstraintVariable(variable: ConstraintVariable) : boolean {
    if (!variable.type) return false;
    if (variable.type === 'flatten' && variable.flatten_value === undefined) return false;
    return true;
  }

  public static hasOneRemainingAxis(plot: PlotlyBuilder): boolean {
    return Object.entries(plot.axes).reduce<number>((acc, [_, axis]) => axis.data ? acc : acc + 1, 0) === 1;
  }

  public static hasDataVarsInPlot(plot: PlotlyBuilder): boolean {
    return Object.entries(plot.axes).filter(([_, axis]) => axis.data?.data_variable !== undefined).length > 0;
  }

  public static getValidPlotTypes(
    plotTypes: PlotlyConfig[],
    axisOptions: AxisOption[],
    includeMap = false,
    n_dimensions: number
  ): PlotlyConfig[] {
    // determine number of properties with numeric scalar in data to be plotted
    const totalLength = axisOptions.length;
    // number of variables that are numeric
    const totalNumericLength = axisOptions
      .filter(option => option.data_variable === undefined)
      .reduce<number>((acc: number, axisOption: AxisOption) => {
      if ((this.isNumeric(axisOption))) { return acc + 1; }
      return acc;
    }, 0) + 1; // adding one accounts for only allowing 1 data var to be plotted for bricks with multiple data vars
    return plotTypes.filter(plotType => {
      if (n_dimensions < plotType.n_dimensions) return false;
      if (plotType.n_dimensions > totalLength) return false;
      if (!includeMap && plotType.map) return false;
      
      // number of plot axes that are required to be numeric
      const totalNumericAxes = Object.entries(plotType.axis_data).reduce<number>((acc: number, [_, val]) => {
          if (val.numeric_only) { return acc + 1 }
          return acc;
      }, 0);
      if (totalNumericAxes > totalNumericLength) {
        return false;
      }
      return true;
    });
  }

  public static isNumeric(axisOption: AxisOption): boolean {
    const {scalar_type, name} = axisOption;
    return scalar_type === 'int'
      || scalar_type === 'date'
      || scalar_type === 'float'
      || scalar_type === 'boolean'
      || name === 'DateTime';
  }
  
  public static tooManyTraces(constraints: Constraint[]) {

    // limits max number of individual plotly traces too 1000
    if (constraints.length === 0) return false;

    const allTraces = constraints
      .map(constraint => constraint.variables)
      .reduce((acc, cv) => acc.concat(cv))
      .filter(constraint => constraint.type === 'series')
      .reduce<number>((acc, cv) => acc * cv.unique_values.length , 1);

    return allTraces > 1000;
  }

  // public static requiresGL(plot: PlotlyBuilder, metadata: ObjectMetadata) {
  public static validateSize(plot: PlotlyBuilder, metadata: ObjectMetadata) {
    // returns [condition for too many traces, condition that requires webGL]
    let nDataPoints = 1;
    Object.entries(plot.axes).forEach(([_, axis]) => {
      if (axis.data?.data_variable === undefined) {
        const i = axis.data.dimension;
        nDataPoints *= metadata.dim_context[i].size;
      }
    });

    if (plot.constraints.length === 0) {
      return [false, nDataPoints > 100_000];
    }

    const allTraces = plot.constraints
      .map(constraint => constraint.variables)
      .reduce((acc, cv) => acc.concat(cv))
      .filter(constraint => constraint.type === 'series')
      .reduce<number>((acc, cv) => acc * cv.unique_values.length, 1);

    return [allTraces > 1000, nDataPoints * allTraces > 100_000]
  }

  public static hasCoordsInDimensions(metadata: ObjectMetadata) {
    const coordProperties = metadata.connects_to_properties.properties;
    // flatten dimensions to check list of dim vars for coord properties
    const allDimVars = metadata.dim_context.reduce((acc, dim) => {
      return [...acc, ...dim.typed_values];
    } , [])
    // check every properties in list of coord properties to make sure there is a dim var with the same value
    const includesCoords = coordProperties.map(propertyName => {
      return allDimVars.filter(d => d.value_type.oterm_name.toLowerCase() === propertyName.toLowerCase()).length > 0;
    })
    return includesCoords.every(x => x === true);
  }

}