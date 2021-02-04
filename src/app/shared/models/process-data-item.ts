// tslint:disable:variable-name

export class ProcessDataItem {
    docs: ProcessDoc[];
    process: Process;
}

export class ProcessDoc {
    category: string;
    description: string;
    id: string;
    type: string;
}

export class Process {
    campaign: string;
    date_start: Date | string | null;
    date_end: Date | string | null;
    id: string;
    person: string;
    process: string;
}
