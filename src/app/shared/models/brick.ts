// tslint:disable:variable-name

import { isEqual } from 'lodash';

export class Brick {

    id: string;
    data_id: string;
    createStatus: string; //
    name: string;
    type: Term;
    template_type: string;
    template_id: string;
    dimensions: BrickDimension[] = [];
    properties: TypedProperty[] = [];
    dataValues: DataValue[] = [];
    dataFileName: string;
    description: string;
    process: Term;
    campaign: Term;
    personnel: Term;
    start_date: Date;
    end_date: Date;
    coreObjectRefsError = false;

    get isEmpty() {
        return isEqual(this, new Brick());
    }

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

export class Term {
    constructor(id?, text?, has_units?) {
        this.id = id;
        this.text = text;
        this.has_units = has_units;
    }
    id: string;
    text: string;
    has_units: boolean;
}

export class ORef {
    constructor(id?, text?) {
        this.id = id;
        this.text = text;
    }
    id: string;
    text: string;
}

export class DataValue {

    constructor(index: number, required?: boolean) {
        this.index = index;
        this.required = required;
    }

    index: number;
    required = false;
    microType: any;
    scalarType: Term;
    units: Term;
    valuesSample: string;
    context: Context[] = [];
    totalCount: number;
    validCount: number;
    invalidCount: number;
    require_mapping: boolean;

    type: Term;

    set typeTerm(t: any) {
        this.type = new Term(t.id, t.text, t.has_units);
        this.microType = t.microtype;
        this.require_mapping = t.require_mapping;
    }

    get typeTerm() { return this.type; }
}

export class Context {
    constructor(
        required?: boolean,
        type?: Term,
        value?: Term,
        units?: Term
    ) {
        this.required = required;
        if (type) {
            this.typeTerm = type;
        }
        this.value = value;
        this.units = units;
    }
    required: boolean;
    // type: Term;
    value: Term;
    units: Term;
    type: Term;
    microType: any;
    scalarType: string;
    invalidValue = false;

    get typeTerm() { return this.type; }
    set typeTerm(t: any) {
        this.type = new Term(t.id, t.text, t.has_units);
        this.microType = t.microtype;
        this.scalarType = t.scalar_type;
    }

    get requireSelect2ForVal() {
        return this.scalarType === 'oterm_ref' ||
        this.scalarType === 'object_ref';
    }
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
    size: number;
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
    require_mapping: boolean;
    dimension: BrickDimension;
    index: number;
    microType: any;
    scalarType: Term = new Term();
    units: Term;
    values: any[] = [];
    context: Context[] = [];
    valuesSample: string; //
    mapCoreType: string; //
    mapCoreProp: string; //
    validCount: number;
    totalCount: number;
    invalidCount: number;
    mapped = false; //
    mapPk = false; //

    type: Term;

    set typeTerm(t: any) {
        this.type = new Term(t.id, t.text, t.has_units);
        this.microType = t.microtype;
        this.require_mapping = t.require_mapping;
    }

    get typeTerm() { return this.type; }
}

export class TypedProperty {
    // TODO: Discuss how to handle ontological terms
    constructor(
        index: number,
        required?: boolean,
        type?: Term,
        microType?: any,
        ) {
        this.index = index;
        this.required = required;
        if (type) { this.typeTerm = type; }
        // this.microType = microType;
    }
    required = true;
    require_mapping: boolean;
    parentCollection: TypedProperty[];
    index: number;
    // type: Term;
    microType: any;
    value: Term | ORef | string;
    invalidValue = false;
    units: Term;
    context: Context[] = [];
    totalCount = 1;
    mappedCount: number;
    scalarType: string;

    type: Term;

    set typeTerm(t: any) {
        this.type = new Term(t.id, t.text, t.has_units);
        this.microType = t.microtype;
        this.require_mapping = t.require_mapping;
        this.scalarType = t.scalar_type;
    }

    get typeTerm() { return this.type; }

    get requireSelect2ForVal() {
        return this.scalarType === 'object_ref'
        || this.scalarType === 'oterm_ref';
    }
}

// this.brick.property.typeTerm = ...

export class MicroType {
    constructor(
        fk?: string,
        valid_units?: string[],
        valid_units_parent?: string[],
        valid_values_parent?: string
    ) {
        this.fk = fk;
        this.valid_units = valid_units;
        this.valid_units_parent = valid_units_parent;
        this.valid_values_parent = valid_values_parent;
    }

    fk: string;
    valid_units: string[];
    valid_units_parent: string[];
    valid_values_parent: string;
}
