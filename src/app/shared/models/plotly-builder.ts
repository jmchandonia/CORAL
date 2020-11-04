import { QueryBuilder } from 'src/app/shared/models/QueryBuilder';
import { PlotlyConfig } from 'src/app/shared/models/plotly-config'; 
import { DimensionContext, TypedValue } from './object-metadata';

export class Axis {
    data: AxisOption;
    title: string;
    showTitle = true;
    labelPattern: string;
    showLabels = true;
    dimIdx?: number;
    dimVarIdx?: number;
    dataVarIdx?: number;
}

export class PlotlyBuilder {

    constructor(isCoreType = false, query?: QueryBuilder) {
        this.isCoreType = isCoreType;
        if (this.isCoreType && query) {
            this.query = query;
        }
    }

    title: string;
    objectId: string;
    query: QueryBuilder;
    isCoreType: boolean;
    plotType: PlotlyConfig;

    plotly_trace: any;
    plotly_layout: any;

    axes: Axes = new Axes();
    constraints: Constraint[] = [];

    setDimensionConstraints(dimensions: DimensionContext[]) {
        this.constraints = [
            ...dimensions.map(dimension => new Constraint(dimension))
        ];
    }
}

class Axes {
    x: Axis = new Axis();
    y: Axis = new Axis();
    z: Axis
} 

export class Series {

}

export enum ConstraintType {
    SERIES = 'series',
    MEAN = 'mean',
    FLATTEN = 'flatten'
}

export class Constraint {

    constructor(dimension: DimensionContext) {
        this.dimension = dimension;
        this.variables = dimension.typed_values.map(value => new ConstraintVariable(value));
    }

    // type: 'mean' | 'series' | 'flatten';
    dimension: DimensionContext;
    variables: ConstraintVariable[];
    constrainByMean = false;
}

export class ConstraintVariable {

    constructor(value: TypedValue) {
        this.value = value;
    }

    value: TypedValue;

    type: 'mean' | 'series' | 'flatten';
    flattenValue: number | string;
}

export class AxisOption { // list of items to be populated in dropdown list of axis menu
    name: string;
    displayName: string; // display including units (if there are any)
    termId: string;
    scalarType: string;
    units?: string;
    dimension?: number;
    dimensionVariable?: number;
    dataVariable?: number;
}

export class DimensionVariable {}