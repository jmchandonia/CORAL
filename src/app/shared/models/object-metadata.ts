// import { Type } from 'class-transformer';
// tslint:disable:variable-name

// export class ObjectMetadata {

//     constructor(args: ObjectMetadata) {
//         Object.assign(this, args);
//     }

//     public id: string;
//     public type: string;
//     public shape: number[];
//     public name: string;
//     @Type(() => ObjectDataInfo)
//     public data: ObjectDataInfo;
//     @Type(() => Dimension)
//     public dimensions: Dimension[];

// }

// export class ObjectDataInfo {

//     constructor(args: ObjectDataInfo) {
//         Object.assign(this, args);
//     }

//     public type: string;
//     public units: string;
//     public scalar_type: string;
// }

export class DimensionValue {

    constructor(args) {
        Object.assign(this, args);
    }
    public type: string;
    public index: number;
    public dim_vars: any[];
}
export class ObjectMetadata {
    public id: string;
    public name: string;
    public array_context: any[];
    public data_type: any;
    public description: string;
    public dim_context: any[]; // dimension and dimension variable data
    public typed_values: any[]; // measurement values and data
}
