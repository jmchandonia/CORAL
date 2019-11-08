import { isEqual } from 'lodash';

// tslint:disable:no-use-before-declare
export class QueryBuilder {
    constructor() { }
    public queryMatch: QueryMatch = new QueryMatch();
    public connectsUpTo: QueryMatch;
    public connectsDownTo: QueryMatch;
    public processesUp: QueryParam[] = [];
    public processesDown: QueryParam[] = [];

    get isEmpty() {
        return isEqual(this, new QueryBuilder());
    }

    get isValid() {
        if (this.isEmpty) { return false; }
        if (this.queryMatch.isValid) { return false; }
        if (this.connectsUpTo && !this.connectsUpTo.isValid) { return false; }
        if (this.connectsDownTo && !this.connectsDownTo.isValid) { return false; }
        for (const processUp of this.processesUp) {
            if (!processUp.isValid) { return false; }
        }
        return true;
    }
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
    public dataModel = '';
    public dataType: string;
    public category: string;
    public params: QueryParam[] = [];

    get isEmpty() {
        return isEqual(this, new QueryMatch());
    }

    isValid() {
        if (this.isEmpty) { return false; }
        for (const param of this.params) {
            if (!param.isValid) { return false; }
        }
        return true;
    }
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

    get isValid() {
        if (
            !this.attribute ||
            !this.matchType ||
            !this.scalarType ||
            !this.keyword.length
        ) {
            return false;
         }
        return true;
    }
}

