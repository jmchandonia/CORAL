import { QueryBuilder } from 'src/app/shared/models/QueryBuilder'

export class MapBuilder {

    constructor(isCoreType = true) {
        this.isCoreType = isCoreType;
    }

    query: QueryBuilder;
    colorField: string = '';
    labelField: string;
    isCoreType: boolean;
    brickId: string;
}