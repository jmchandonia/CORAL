import { QueryBuilder } from 'src/app/shared/models/QueryBuilder'
import { AxisOption } from 'src/app/shared/models/plotly-builder';

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
}