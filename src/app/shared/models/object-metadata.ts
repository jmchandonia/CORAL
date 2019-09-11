
import { Type } from 'class-transformer';

export class ObjectMetadata {

    constructor(args: ObjectMetadata) {
        Object.assign(this, args);
    }

    public id: string;
    public type: string;
    public shape: number[];
    public name: string;
    @Type(() => ObjectDataInfo)
    public data: ObjectDataInfo;
    @Type(() => Dimension)
    public dimensions: Dimension[];

}

export class ObjectDataInfo {

    constructor(args: ObjectDataInfo) {
        Object.assign(this, args);
    }

    public type: string;
    public units: string;
    // tslint:disable-next-line:variable-name
    public scalar_type: string;
}

export class Dimension {

    constructor(args) {
        Object.assign(this, args);
    }
    public type: string;
    public index: number;
    // tslint:disable-next-line:variable-name
    public dim_vars: any[];
}
