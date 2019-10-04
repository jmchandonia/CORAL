// tslint:disable:variable-name

export class Brick {
    id: string;
    createStatus: string; //
    name: string;
    type: string;
    template_id: string;
    dimensions: BrickDimension[] = [];
    properties: TypedProperty[] = [];
    data_file_name: string;
}

export class Term {
    id: string;
    name: string;
}

export class BrickDimension {
    brick: Brick;
    index: number;
    type: Term = new Term();
    variables: DimensionVariable[] = [];
}

export class DimensionVariable {
    dimension: BrickDimension;
    index: number;
    type: Term = new Term();
    scalarType: string;
    values: any[] = [];
    valuesSameple: string; //
    mapCoreType: string; //
    mapCoreProp: string; //
    mappedCount: number; //
    totalcount: number; //
    mapped = false; //
    mapPk = false; //
}

export class TypedProperty {
    parentCollection: TypedProperty[];
    index: number;
    type: Term = new Term();
    value: string;
    units: Term = new Term();
}