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

    constructor(dimension: DimensionContext, dimIdx: number, disabled = false) {
        this.dim_idx = dimIdx;
        this.dimension = dimension;
        this.has_unique_indices = dimension.has_unique_indices;
        this.disabled = disabled;
        // this.variables = dimension.typed_values.map((value, idx) => new ConstraintVariable(value, idx));
        if (!this.has_unique_indices) {
            let correspondsToOneVar = this.dimension.typed_values
                .map(typedValue => {
                    return typedValue.values.values.reduce((acc, value) => acc.includes(value) && value !== null ? acc : [...acc, value], []);
                })
                .map(typedValue => typedValue.length)
                .reduce((acc, typedValue) => typedValue === this.dimension.size, false);
            if (correspondsToOneVar) {
                // brick does not have unique values but is also not combinatoric
                const concatTypedValue = {
                    value_with_units: dimension.typed_values.reduce<string>((acc, cur, i) => {
                        let newValWithUnits = cur.value_with_units;
                        if (i < dimension.typed_values.length - 1) { newValWithUnits += ', ' }
                        return acc + newValWithUnits;
                    }, '')
                
                } as TypedValue;
                this.variables = [new ConstraintVariable(concatTypedValue, -1, dimension.typed_values)];
                this.concat_variables = true;
            } else {
                // brick is combinatoric and doesnt depend on specific values from other dim vars
                this.variables = dimension.typed_values.map((value, idx) => new ConstraintVariable(value, idx,null, this.has_unique_indices));
            }
        } else {
            this.variables = dimension.typed_values.map((value, idx) => new ConstraintVariable(value, idx, null, this.has_unique_indices));
        }
    }
    has_unique_indices = false;
    disabled = false;
    dim_idx: number;
    dimension: DimensionContext;
    variables: ConstraintVariable[];
    constrain_by_mean = false;
    concat_variables = false;
}

export class ConstraintVariable {

    constructor(value: TypedValue, index: number, concatValues?: TypedValue[], has_unique_indices = true) {
        this.dim_var_idx = index;
        this.value = value;
        if (concatValues) {
            this.unique_values = [];
            for (let i = 0; i < concatValues[0].values.values.length; i++) {
                let newValue = '';
                for (let j = 0; j < concatValues.length; j++) {
                    newValue += concatValues[j].values.values[i] !== null ? concatValues[j].values.values[i] : 'N/A';
                    if (concatValues[j])
                    if (j < concatValues.length - 1) {
                        newValue += ', '
                    }
                }
                this.unique_values.push({display: newValue, index: i});
            }
        } else {
            this.unique_values = this.value.values.values.reduce((acc, value, index) => {
                if (!acc.find(d => d.display === value)) {
                    // if its a combinatoric brick set it by the index of the unique value, otherwise position in array
                    return [...acc, {display: value, index: has_unique_indices ? index : acc.length}];
                }
                return acc;
            }, []);
        }
    }

    dim_var_idx: number;
    selected_value: number;
    value: TypedValue;
    unique_values: UniqueValue[]

    type: 'mean' | 'series' | 'flatten';
    flatten_value: number | string;
    series_label_pattern: string;
    invalid_label_pattern = false;
}

export interface UniqueValue {
    display: string | number;
    index: number;
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