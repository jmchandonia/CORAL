// tslint:disable:no-use-before-declare
export class QueryBuilder {
    constructor() { }
    public queryMatch: QueryMatch = new QueryMatch();
    public connectsUpTo: QueryMatch;
    public connectsDownTo: QueryMatch;
    public processesUp: QueryParam[] = [];
    public processesDown: QueryParam[] = [];
}

export class QueryMatch {
    constructor(
        dType?: string,
        dModel?: string
    ) {
        this.dataType = dType;
        this.dataModel = dModel;
        this.params = [];
    }
    public dataModel: string;
    public dataType: string;
    public category: string;
    public params: QueryParam[] = [];
}

export class QueryParam {
    constructor(
        attr?: string,
        match?: string,
        key?: string,
        scalar?: string
    ) {
        this.attribute = attr;
        this.matchType = match;
        this.keyword = key;
        this.scalarType = scalar;
    }
    public attribute: string;
    public matchType: string;
    public scalarType: string;
    public keyword = '';
}

