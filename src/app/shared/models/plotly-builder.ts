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

    get isValid(): boolean {
        if (!this.plotType) return false;

        for (const [_, val] of Object.entries(this.axes)) {
            if (!val.data) return false;
        }

        for (const constraint of this.constraints) {
            if(!constraint.isValid) return false;
        }
        return true;
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

    get isValid(): boolean {
        if (this.constrainByMean) return true;
        for (const variable of this.variables) {
            if (!variable.isValid) return false;
        }
        return true;
    }

    // type: 'mean' | 'series' | 'flatten';
    dimension: DimensionContext;
    variables: ConstraintVariable[];
    constrainByMean = false;
}

export class ConstraintVariable {

    constructor(value: TypedValue) {
        this.value = value;
        this.uniqueValues = this.value.values.values.reduce((acc, value) => {
            if (!acc.includes(value)) {
                return [...acc, value];
            }
            return acc;
        }, []);
    }

    get isValid(): boolean {
        if (this.type === undefined) return false;
        if (this.type === ConstraintType.FLATTEN && this.flattenValue === undefined) return false;
        return true;
    }

    value: TypedValue;
    uniqueValues: number[] | string[]; // remove repeating instances of the same value for dropdown

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