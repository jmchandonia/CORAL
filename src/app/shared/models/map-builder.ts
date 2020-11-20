import { QueryBuilder } from './QueryBuilder'
import { AxisOption, Constraint } from './plotly-builder';
import { DimensionContext } from  './object-metadata';

export class MapBuilder {

    constructor(isCoreType = true) {
        this.isCoreType = isCoreType;
    }

    query: QueryBuilder;
    colorField: AxisOption;
    labelField: AxisOption;
    colorFieldScalarType: string;
    isCoreType: boolean;
    brickId: string;
    constraints: Constraint[];
    dimWithCoords: number;

    setConstraints(dims: DimensionContext[]): void {
        // we only need to constraint dimensions for data vars
        // the only other option available to the user is options from the same dimension (wouldnt need constraining)
        this.constraints = dims.map((dim, idx) => {
            if (idx === this.dimWithCoords) return new Constraint(dim, idx, true);
            return new Constraint(dim, idx, this.colorField?.data_variable === undefined && this.labelField?.data_variable === undefined);
        });
    }

    setLatLongDimension(options: AxisOption[]): void {
        this.dimWithCoords = options.find(option => {
            return option.name.toLowerCase() === 'latitude' || option.name.toLowerCase() === 'longitude';
        }).dimension;
    }
}