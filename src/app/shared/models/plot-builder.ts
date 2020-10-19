
// tslint:disable:variable-name

import { ObjectMetadata, DimensionContext, TypedValue } from './object-metadata';

export class Config {
    title: string;
    x: Dimension;
    y: Dimension;
    z: Dimension;
}

export class PlotBuilder {
    public objectId: string;
    public data: any = {
        x: '' as any,
        y: '' as any,
    };
    public config: Config = new Config();
    public plotly_trace: any;
    public plotly_layout: any;
    public constraints: any;
}

export class Dimension {

    constructor(
        dimensionData: DimensionContext[],
        dataVars: TypedValue[]
        ) {
        this.dimensionMetadata = dimensionData;
        this.dataValueMetadata = dataVars;
    }

    title = '';
    label_pattern: string;
    show_title = true;
    show_labels = true;
    dimensionMetadata: DimensionContext[];
    dataValueMetadata: TypedValue[];
    dimVars: TypedValue[];
}


