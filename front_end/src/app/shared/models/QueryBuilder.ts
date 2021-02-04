import { isEqual } from 'lodash';

// tslint:disable:no-use-before-declare
export class QueryBuilder {
    constructor() { }
    public queryMatch: QueryMatch = new QueryMatch();
    public connectsUpTo: QueryMatch;
    public connectsDownTo: QueryMatch;
    public processesUp: QueryParam[] = [];
    public processesDown: QueryParam[] = [];
    public searchAllProcessesUp = false;
    public searchAllProcessesDown = false;
    parentProcesses: Process;

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
        data?: QueryMatchData
    ) {
        if (data) {
            this.dataType = data.dataType;
            this.dataModel = data.dataModel;
            this.category = data.category;
        }
        this.params = [];
    }
    public dataModel = '';
    public dataType: string;
    public category: string;
    public params: QueryParam[] = [];

    get isEmpty() {
        return isEqual(this, new QueryMatch());
    }

    get data() {
        return {
            dataType: this.dataType,
            dataModel: this.dataModel,
            category: this.category
        }
    }

    isValid() {
        if (this.isEmpty) { return false; }
        for (const param of this.params) {
            if (!param.isValid) { return false; }
        }
        return true;
    }
}

export interface QueryMatchData {
    dataType: string;
    dataModel: string;
    category: string;
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
    public term?: string;

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

export class Process {
    // interface for defining process inputs and outputs for queries from provenance graph
    constructor(processInputs: string[], processOutputs: string[]) {
        this.processInputs = processInputs;
        this.processOutputs = processOutputs;
    }

    processInputs: string[];
    processOutputs: string[];
}
