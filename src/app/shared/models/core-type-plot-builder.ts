import { QueryBuilder } from './QueryBuilder';
import { Config } from './plot-builder';
import { PlotlyConfig } from './plotly-config';

export class CoreTypePlotBuilder {

    constructor() {
        this.axes = [
            new CoreTypeAxis(),
            new CoreTypeAxis()
        ]
    }

    query: QueryBuilder;
    public data: any = {
        x: '' as any, 
        y: '' as any
    };
    plotly_trace: any;
    plotly_layout: any;
    config: Config = new Config();
    axes: CoreTypeAxis[];
    axisTitles: any = {
        x: {
            title: '',
            showTitle: true
        },
        y: {
            title: '',
            showTitle: true
        },
    }
}

export class CoreTypeAxis {
    name: string;
    scalar_type: string;
    term_id: string;
    propAxisLabelPattern?: string;
}