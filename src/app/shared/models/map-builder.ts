import { QueryBuilder } from './QueryBuilder'
import { AxisOption, Constraint, BrickFilter } from './plotly-builder';
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
    latDimIdx: number;
    longDimIdx: number;
    constrainingRequired = false; // for dynamic type dimensions
    multipleCoordinates = false; //TODO: edge case where bricks have more thant one instance of 'latitude and longitude'
    logarithmicColorScale = false;

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
        const latLongOptions = options.filter(option => {
            return option.name.toLowerCase() === 'latitude' || option.name.toLowerCase() === 'longitude';
        });

        if (latLongOptions.length !== 2) {
            this.multipleCoordinates = true;
        } else {
            this.dimWithCoords = latLongOptions[0].dimension;
            this.latDimIdx = latLongOptions.find(d => d.name.toLowerCase() === 'latitude').dimension_variable;
            this.longDimIdx = latLongOptions.find(d => d.name.toLowerCase() === 'longitude').dimension_variable;
        }
    }

    createPostData(): BrickFilter {
        let variable = [
            `${this.dimWithCoords + 1}/${this.latDimIdx + 1}`,
            `${this.dimWithCoords + 1}/${this.longDimIdx + 1}`
        ];

        let constant = {};

        this.constraints
            .filter(c => !c.disabled)
            .forEach(constraint => {
                const dim_idx = constraint.dim_idx;
                if (constraint.concat_variables || constraint.has_unique_indices) {
                    if (constraint.variables[0].type === 'flatten') {
                        constant = {...constant, [`${dim_idx + 1}`]: constraint.variables[0].selected_value + 1};
                    }
                } else {
                    constraint.variables.forEach(dimVar => {
                        if (dimVar.type === 'flatten') {
                            constant = {...constant, [dim_idx]: dimVar.selected_value + 1};
                        }
                    });
                }
        })

        const postData: BrickFilter = {variable, constant, z: 1};
        if (this.labelField) {
            postData['point-labels'] = `${this.labelField.dimension + 1}/${this.labelField.dimension_variable + 1}`;
        };

        if (this.colorField.dimension !== undefined) {
            postData.data = `${this.colorField.dimension + 1}/${this.colorField.dimension_variable + 1}`;
        }
        return postData;
    }
}