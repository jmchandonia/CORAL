import { QueryBuilder } from 'src/app/shared/models/QueryBuilder';
import { PlotlyConfig } from 'src/app/shared/models/plotly-config'; 
import { DimensionContext, TypedValue, ObjectMetadata } from './object-metadata';

export class Axis {
    data: AxisOption;
    title: string;
    show_title = true;
    label_pattern: string;
    show_labels = true;
    dim_idx?: number;
    dim_var_idx?: number;
    data_var_idx?: number;
    show_err_margin = true;
    logarithmic = false;
}

export class PlotlyBuilder {

    constructor(core_type = false, query?: QueryBuilder) {
        this.core_type = core_type;
        if (this.core_type && query) {
            this.query = query;
        }
    }

    title: string;
    object_id: string;
    query: QueryBuilder;
    core_type: boolean;
    plot_type: PlotlyConfig;

    plotly_trace: any;
    plotly_layout: any;

    axes: Axes = new Axes();
    constraints: Constraint[] = [];

    setDimensionConstraints(dimensions: DimensionContext[], metadata?: ObjectMetadata) {
        this.constraints = [
            ...dimensions.map((dimension, idx) => new Constraint(
                dimension,
                metadata ? metadata.dim_context.indexOf(dimension) : idx
            ))
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

    constructor(dimension: DimensionContext, dimIdx: number) {
        this.dim_idx = dimIdx;
        this.dimension = dimension;
        this.variables = dimension.typed_values.map((value, idx) => new ConstraintVariable(value, idx));
    }
    dim_idx: number;
    dimension: DimensionContext;
    variables: ConstraintVariable[];
    constrain_by_mean = false;
}

export class ConstraintVariable {

    constructor(value: TypedValue, index: number) {
        this.dim_var_idx = index;
        this.value = value;
        this.unique_values = this.value.values.values.reduce((acc, value) => {
            if (!acc.includes(value)) {
                return [...acc, value];
            }
            return acc;
        }, []);
    }

    dim_var_idx: number;
    selected_value: number;
    value: TypedValue;
    unique_values: number[] | string[]; // remove repeating instances of the same value for dropdown

    type: 'mean' | 'series' | 'flatten';
    flatten_value: number | string;
    series_label_pattern: string;
    invalid_label_pattern = false;
}

export class AxisOption { // list of items to be populated in dropdown list of axis menu
    name: string;
    display_name: string; // display including units (if there are any)
    term_id: string;
    scalar_type: string;
    units?: string;
    dimension?: number;
    dimension_variable?: number;
    data_variable?: number;
}

export class DimensionVariable {}