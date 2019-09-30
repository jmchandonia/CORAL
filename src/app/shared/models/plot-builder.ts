// export class PlotBuilder {
//     public plotType = '';
//     public title = '';
//     public titleChecked: boolean;
//     public dimensions: Dimension[] = [];
// }

// export class Dimension {
//     public fromDimension = '';
//     public axisTitle = '';
//     public labelPattern = '';
//     public displayAxisTitle = true;
//     public displayHoverLabels = true;
//     public displayHoverLabelsAs = '';
//     public displayAxisLabels = true;
//     public displayAxisLabelsAs: string[] = [];
// }

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
    }

    type: string;
    dimVars: any[];

    get selectedDimVars() {
        return [...this.dimVars.filter(d => d.selected)];
    }
}
