// tslint:disable:variable-name

export class Brick {
    id: string;
    createStatus: string; //
    name: string;
    type: string;
    template_id: string;
    dimensions: BrickDimension[] = [];
    properties: TypedProperty[] = [];
    dataValues: DataValue[] = [];
    data_file_name: string;

    resetDimensionIndices() {
        this.dimensions.forEach((dimension, index) => {
            dimension.index = index;
        });
    }

    resetDataValueIndices() {
        this.dataValues.forEach((dataValue, index) => {
            dataValue.index = index;
        });
    }

    toJson() {
        const cache = [];
        const res = JSON.stringify(this, (key, value) => {
            if (typeof value === 'object' && value !== null) {
                if (cache.indexOf(value) !== -1) {
                    // Duplicate reference found (prevents circular JSON)
                    try {
                        // If this value does not reference a parent it can be deduped
                        return JSON.parse(JSON.stringify(value));
                    } catch (error) {
                        // discard key if value cannot be deduped
                        return;
                    }
                }
                // Store value in our collection
                cache.push(value);
            }
            return value;
        });
        return res;
      }
}

export class DataValue {

    constructor(index: number, required?: boolean) {
        this.index = index;
        this.required = required;
    }

    index: number;
    required = false;
    type: Term;
    scalarType: Term;
    units: Term;
}

export class Term {
    constructor(id?, text?) {
        this.id = id;
        this.text = text;
    }
    id: string;
    text: string;
}

export class BrickDimension {
    constructor(
        brick: Brick,
        index: number,
        required?: boolean
    ) {
        this.brick = brick;
        this.index = index;
        this.required = required;
    }
    brick: Brick;
    index: number;
    type: Term;
    required: boolean;
    // type: string;
    variables: DimensionVariable[] = [];

    resetDimVarIndices() {
        this.variables.forEach((variable, idx) => {
            variable.index = idx;
        });
    }
}

export class DimensionVariable {
    constructor(dimension, index, required?) {
        this.dimension = dimension;
        this.index = index;
        this.required = required;
    }
    required = true;
    dimension: BrickDimension;
    index: number;
    type: Term;
    scalarType: Term = new Term();
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
    constructor(index: number, required?: boolean) {
        this.index = index;
        this.required = required;
    }
    required = true;
    parentCollection: TypedProperty[];
    index: number;
    type: Term;
    value: Term = new Term();
    units: Term;
}
