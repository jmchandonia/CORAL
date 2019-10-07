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
    id: string;
    name: string;
}

export class BrickDimension {
    constructor(
        brick: Brick,
        index: number
    ) {
        this.brick = brick;
        this.index = index;
    }
    brick: Brick;
    index: number;
    // type: Term = new Term();
    type: string;
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
    // type: Term = new Term();
    type: string;
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
    // TODO: Discuss how to handle ontological terms
    parentCollection: TypedProperty[];
    index: number;
    // type: Term = new Term();
    type: string;
    value: string;
    // units: Term = new Term();
    units: string;
}
