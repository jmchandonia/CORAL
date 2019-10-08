
// tslint:disable:variable-name

export class Config {
    title: string;
    x: Dimension;
    y: Dimension;
    z: Dimension;
}

export class PlotBuilder {
    public objectId: string;
    public data: any = {
        x: '',
        y: '',
    };
    public config: Config = new Config();
    public plotly_trace: any;
    public plotly_layout: any;
    public constraints: any;
}

export class Dimension {
    title = '';
    label_pattern: string;
    show_title = true;
    show_labels = true;
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
