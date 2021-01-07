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
    show_tick_labels = true;
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
    multi_data_vars = false;
    urlPostData?: BrickFilter; // bricks created from urls dont need to use createPostData()

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

    createPostData(): BrickFilter {
        const m = +this.multi_data_vars
        let variable: string[];
        const {x, y} = this.axes;
        if (this.axes.z) {
            variable = [
                `${x.data.dimension + 1 + m}/${x.data.dimension_variable + 1}`,
                `${y.data.dimension + 1 + m}/${y.data.dimension_variable + 1}`
            ];
        } else {
            // we have to invert the axes if its a horizontal barchart
            variable = this.plot_type.name === 'Horizontal Barchart'
                ? [`${y.data.dimension + 1 + m}/${y.data.dimension_variable + 1}`]
                : [`${x.data.dimension + 1 + m}/${x.data.dimension_variable + 1}`];
        }

        const label_format = {};

        this.constraints.forEach(constraint => {
            if (constraint.concat_variables && constraint.variables[0].type === 'series') {
                variable.push(`${constraint.dim_idx + 1}`);
                /////
                label_format[`${constraint.dim_idx + 1 + m}`] = constraint.variables[0].series_label_pattern;
                /////
            } else {
                constraint.variables.forEach(dimVar => {
                    if (dimVar.type === 'series') {
                        variable.push(`${constraint.dim_idx + 1 + m}/${dimVar.dim_var_idx + 1}`);
                        label_format[`${constraint.dim_idx + 1 + m}/${dimVar.dim_var_idx + 1}`] = dimVar.series_label_pattern;
                    }
                })
            }
        });

        const constant = this.constraints.reduce((acc, constraint) => {
            const dim_idx = constraint.dim_idx + 1 + m;
            if (constraint.has_unique_indices || constraint.concat_variables) {
                if (constraint.variables[0].type !== 'flatten') return acc;
                return {
                    ...acc, 
                    [dim_idx]: constraint.variables[0].selected_value + 1
                };
            }
            return {
                ...acc,
                ...constraint.variables.reduce((acc, dimVar) => {
                    const dim_var_idx = dimVar.dim_var_idx + 1;
                    if (dimVar.type !== 'flatten') return acc;
                    return {...acc, [`${dim_idx}/${dim_var_idx}`]: dimVar.selected_value + 1}
                }, {})
            }
        }, {});
        const postData: BrickFilter = {constant, variable, 'label-format': label_format};
        if (this.axes.z) {
            postData.z = true;
        }

        if (this.multi_data_vars) {
            if (this.plot_type.name === 'Horizontal Barchart') {
                constant['1'] = this.axes.x.data.data_variable + 1;
            } else {
                constant['1'] = this.axes.z
                    ? this.axes.z.data.data_variable + 1
                    : this.axes.y.data.data_variable + 1;
            }
        }
        return postData;
    }

    deflate() {
        // returns minified data to store plot in shareable URL
        return encodeURIComponent(JSON.stringify(
            {
                flt: this.createPostData(),
                axes: Object.entries(this.axes).reduce((acc, [key, value]) => {
                    return {
                        ...acc,
                        [key]: {
                            lg: value.logarithmic,
                            e: value.show_err_margin,
                            lb: value.show_labels,
                            tl: value.show_tick_labels,
                            t: value.show_title ? value.title : ''
                        }
                    };
                }, {}),
                plt: {
                    plotly_trace: this.plot_type.plotly_trace,
                    plotly_layout: this.plot_type.plotly_layout,
                    n: this.plot_type.name
                }
            }
        ));
    }

    getPlotShareableUrl() {
        if (!this.core_type) {
            return `${window.location.href}?zip=${this.deflate()}`;
        }
    }
}

export interface BrickFilter {
    constant: object;
    variable: string[];
    z?: boolean | number;
    data?: string; // for selecting dimension values to plot as points in map builder
    'point-labels'?: string;
    'label-format'?: any;
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

        let correspondsToOneVar = this.dimension.typed_values
            .map(typedValue => {
                return typedValue.values.values.reduce((acc, value) => acc.includes(value) && value !== null ? acc : [...acc, value], []);
            })
            .map(typedValue => typedValue.length)
            .reduce((acc, typedValue) => typedValue === this.dimension.size, false);

        if (this.has_unique_indices || correspondsToOneVar) {
            const concatTypedValue = {
                value_with_units: dimension.typed_values.reduce<string>((acc, curr, i) => {
                    let newValWithUnits = curr.value_with_units;
                    if (i < dimension.typed_values.length - 1) { newValWithUnits += ', '; }
                    return acc + newValWithUnits;
                }, '')
            } as TypedValue;
            this.variables = [new ConstraintVariable(concatTypedValue, -1, dimension.typed_values)];
            this.concat_variables = true;
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