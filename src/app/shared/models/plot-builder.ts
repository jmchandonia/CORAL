
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
}

export class DimensionRef {

    constructor(type, dimVars) {
        this.type = type;
        this.dimVars = dimVars;
        this.resetLabels();
    }

    type: string;
    dimVars: any[];
    _labels: string[];

    resetLabels() {
        if (this.dimVars.length === 1) {
            this.labels = ['#V1'];
        } else {
            this.labels = this.dimVars.map((d, i) => {
                return d.selected ? `${d.value}=#V${i + 1}` : '';
            });
        }
    }

    set labels(l: string[]) {
        this._labels = l;
    }

    get labels() {
        return this._labels.filter(label => label.length);
    }

    get selectedDimVars() {
        return [...this.dimVars.filter(d => d.selected)];
    }
}
