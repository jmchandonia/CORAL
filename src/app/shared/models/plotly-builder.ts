import { QueryBuilder } from 'src/app/shared/models/QueryBuilder';
import { PlotlyConfig } from 'src/app/shared/models/plotly-config'; 

export class Axis {
    // fromField: string | AxisOption; // will only be AxisOption
    data: AxisOption = new AxisOption();
    title: string;
    showTitle = true;
    labelPattern: string;
    showLabels = true;
}

export class PlotlyBuilder {

    constructor(isCoreType = false, query?: QueryBuilder) {
        this.isCoreType = isCoreType;
        if (this.isCoreType && query) {
            this.query = query;
        }
    }

    title: string;
    objectId: string;
    query: QueryBuilder;
    isCoreType: boolean;
    plotType: PlotlyConfig;

    plotly_trace: any;
    plotly_layout: any;

    axes: Axes = new Axes();

    // axes: {
    //     x: Axis = new Axis(),
    //     y?: Axis,
    //     z?: Axis|Series
    // } = {};
}

// export class Axis {
//     fromField: string | AxisOption; // will only be AxisOption
//     title: string;
//     showTitle = true;
//     labelPattern: string;
//     showLabels = true;
// }

class Axes {
    x: Axis = new Axis();
    y: Axis = new Axis();
    z: Axis | Series
} 

export class Series {

}

export class AxisOption { // list of items to be populated in dropdown list of axis menu
    name: string;
    displayName: string; // display including units (if there are any)
    termId: string;
    scalarType: string;
    units?: string;
    dimension?: number;
    dimensionVariable?: number;
}

export class DimensionVariable {}