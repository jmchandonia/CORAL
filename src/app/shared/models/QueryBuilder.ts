export class QueryBuilder {
    constructor() { }
    public queryMatch: QueryMatch;
    public connectsUpTo: QueryMatch;
    public connectsDownTo: QueryMatch;
    public processesUp: QueryParam[] = [];
    public processesDown: QueryParam[] = [];
}

export class QueryMatch {
    constructor(dType?: string) { 
        this.dataType = dType;
        this.params = [];
    }
    public dataType: string;
    public params: QueryParam[];
}

export class QueryParam {
    constructor(
        attr?: string,
        match?: string,
        key?: string
    ) { 
        this.attribute = attr;
        this.matchType = match;
        this.keyword = key;
    }
    public attribute: string = '';
    public matchType: string = '';
    public keyword: string = '';
}
