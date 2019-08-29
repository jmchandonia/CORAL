export class QueryBuilder {
    constructor() { }
    public queryMatch: QueryMatch;
    public connectsUpTo: QueryMatch;
    public connectsDownTo: QueryMatch;
    public processesUp: QueryParam[];
    public processesDown: QueryParam[];
}

export class QueryMatch {
    constructor() { }
    public dataType: string;
    public params: QueryParam[];
}

export class QueryParam {
    constructor() { }
    public attribute: string;
    public matchType: string;
    public keyword: string;
}
