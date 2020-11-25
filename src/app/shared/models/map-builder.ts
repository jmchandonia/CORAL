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
    constrainingRequired = false; // for dynamic type dimensions

    setConstraints(dims: DimensionContext[]): void {
        // we only need to constraint dimensions for data vars
        // the only other option available to the user is options from the same dimension (wouldnt need constraining)
        if (!this.constraints) {
            this.constraints = dims.map((dim, idx) => {
                if (idx === this.dimWithCoords) return new Constraint(dim, idx, true);
                return new Constraint(dim, idx, this.colorField?.data_variable === undefined && this.labelField?.data_variable === undefined);
            });
            // this.constrainingRequired = this.constraints.reduce((acc, c) => +c.disabled, 0) === 0;
        } else {
            if (this.labelField?.data_variable !== undefined || this.colorField?.data_variable !== undefined) {
                // this.constraints.forEach((constraint, idx) => {
                //     if (idx !== this.dimWithCoords) { constraint.disabled = false; }
                // });
                this.constraints = [
                    ...this.constraints.map((constraint, idx) => {
                        if (idx === this.dimWithCoords) {
                            return {...constraint, disabled: true};
                        }
                        return {...constraint, disabled: false};
                    })
                ];
            } else {
                // this.constraints.forEach((constraint, idx) => constraint.disabled = true);
                this.constraints = [...this.constraints.map(constraint => ({...constraint, disabled: true}))]
            }
        }
        this.constrainingRequired = this.constraints.reduce((acc, c) => +c.disabled, 0) === 0;
    }

    setLatLongDimension(options: AxisOption[]): void {
        this.dimWithCoords = options.find(option => {
            return option.name.toLowerCase() === 'latitude' || option.name.toLowerCase() === 'longitude';
        }).dimension;
    }
}