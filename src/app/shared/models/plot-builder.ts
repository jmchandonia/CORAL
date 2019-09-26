export class PlotBuilder {
    public plotType = '';
    public title = '';
    public titleChecked: boolean;
    public dimensions: Dimension[] = [];
}

export class Dimension {
    public fromDimension: string;
    public displayValuesFrom: string[] = [];
    public axisTitle: string;
    public displayAxisTitle: boolean;
    public displayHoverLabels: boolean;
    public displayHoverLabelsAs: string;
    public displayAxisLabels: boolean;
    public displayAxisLabelsAs: string[] = [];
}