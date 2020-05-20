// tslint:disable:variable-name

export class ObjectMetadata {
    public id: string;
    public name: string;
    public array_context: ArrayContext[];
    public data_type: OTerm;
    public description: string;
    public dim_context: DimensionContext[]; // dimension and dimension variable data
    public typed_values: TypedValue[]; // measurement values and data
}

export class
    DimensionContext {
    data_type: OTerm;
    size: number;
    typed_values: TypedValue[];
}

export interface ArrayContext {
    value: Value;
    value_type: OTerm;
}

export interface Value {
    scalar_type: string;
    value: string;
}

export interface TypedValue {
    value_context: any[]; // TODO: double check format for contextons
    value_no_units: string;
    value_type: OTerm;
    value_with_units: string;
    selected?: boolean; // for dimension variable checkboxes in plotting
}

export interface OTerm {
    oterm_name: string;
    oterm_ref: string;
}


