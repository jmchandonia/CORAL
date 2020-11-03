import { QueryBuilder } from 'src/app/shared/models/QueryBuilder';
import { PlotlyConfig } from 'src/app/shared/models/plotly-config'; 
import { DimensionContext } from './object-metadata';

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
    type: 'mean' | 'series' | 'flatten';
    dimension: DimensionContext;
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