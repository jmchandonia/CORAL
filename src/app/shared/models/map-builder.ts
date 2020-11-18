import { QueryBuilder } from './QueryBuilder'
import { AxisOption, Constraint } from './plotly-builder';
import { DimensionContext } from  './object-metadata';

export class MapBuilder {

    constructor(isCoreType = true) {
        this.isCoreType = isCoreType;
    }

    query: QueryBuilder;
    colorField: AxisOption;
    colorFieldScalarType: string;
    labelField: string;
    isCoreType: boolean;
    brickId: string;
    constraints: Constraint[];

    setConstraints(dims: DimensionContext[], dimIdx: number, dataVarIdx: number) {
        // if (dataVarIdx !== undefined) {
            this.constraints = dims.map((dim, idx) => {
                for (const dimVar of dim.typed_values) {
                    if (
                        dimVar.value_no_units.toLowerCase() === 'latitude'
                        || dimVar.value_no_units.toLowerCase() === 'longitude'
                    ) {
                        return new Constraint(dim, idx, true);
                    }
                }
                if (dataVarIdx !== undefined) return new Constraint(dim, idx, false);
                return new Constraint(dim, idx, idx > dimIdx);
            })
        // }
    }

    // setConstraints(dims: DimensionContext[], dimIdx: number, dataVarIdx: number)  {
        
    //     if (dataVarIdx !== undefined) {
    //         // if were plotting data value then we need constraints on all dimensions
    //         this.constraints = dims
    //             .filter(dim => {
    //                 // we always want to remove the dimension that contains lat and long (it will be plotted as a series)
    //                 for (const dimVar of dim.typed_values) {
    //                     if (dimVar.value_no_units.toLowerCase() === 'latitude') return false;
    //                     if (dimVar.value_no_units.toLowerCase() === 'longitude') return false;
    //                 }
    //                 return true;
    //             })
    //             .map((dim, idx) => new Constraint(dim, idx));
    //     } else {
    //         // otherwise we only need constraints up to the highest dimension from the color or label
    //         this.constraints = dims
    //             .filter((dim, idx) => {
    //                 for (const dimVar of dim.typed_values) {
    //                     if (dimVar.value_no_units.toLowerCase() === 'latitude') return false;
    //                     if (dimVar.value_no_units.toLowerCase() === 'longitude') return false;
    //                 }
    //                 return idx <= dimIdx
    //             })
    //             .map((dim, idx) => new Constraint(dim, idx));
    //     }
    // }
}