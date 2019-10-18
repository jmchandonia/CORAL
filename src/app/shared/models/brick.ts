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

    resetDimensionIndices() {
        this.dimensions.forEach((dimension, index) => {
            dimension.index = index;
        });
    }
}

export class Term {
    constructor(id?, text?) {
        this.id = id;
        this.text = text;
    }
    id: string;
    name: string;
}

export class BrickDimension {
    constructor(
        brick: Brick,
        index: number,
        editable?: boolean
    ) {
        this.brick = brick;
        this.index = index;
        this.editable = editable;
    }
    brick: Brick;
    index: number;
    type: Term;
    editable = true;
    // type: string;
    variables: DimensionVariable[] = [];

    resetDimVarIndices() {
        this.variables.forEach((variable, idx) => {
            variable.index = idx;
        });
    }
}

export class DimensionVariable {
    constructor(dimension, index) {
        this.dimension = dimension;
        this.index = index;
    }
    dimension: BrickDimension;
    index: number;
    type: Term;
    // type: string;
    // scalarType: string;
    scalarType: Term;
    units: Term;
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
    // TODO: Discuss how to handle ontological terms
    constructor(index: number, editable?: boolean) {
        this.index = index;
        this.editable = editable;
    }
    editable = true;
    parentCollection: TypedProperty[];
    index: number;
    type: Term;
    // type: string;
    value: Term;
    units: Term;
    // units: string;
}
