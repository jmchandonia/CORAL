// tslint:disable:variable-name

export class ObjectMetadata {
    public id: string;
    public name: string;
    public array_context: any[];
    public data_type: any;
    public description: string;
    public dim_context: any[]; // dimension and dimension variable data
    public typed_values: any[]; // measurement values and data
}
